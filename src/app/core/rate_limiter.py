import time
from dataclasses import dataclass
from typing import Optional

from fastapi import Request
import redis.asyncio as aioredis

from src.app.core.logging import get_logger
logger = get_logger(__name__)

@dataclass(frozen=True)
class RateLimitConfig:
    limit: int
    window_seconds: int

@dataclass(frozen=True)
class RateLimitResult:
    allowed: bool
    remaining: int
    limit: int
    retry_after: Optional[int] = None
    reset_after: Optional[int] = None

# Default configurations
ANALYZE_RATE_LIMIT = RateLimitConfig(
    limit=10,
    window_seconds=60,
)

PUBLIC_RATE_LIMIT = RateLimitConfig(
    limit=60,
    window_seconds=60,
)

class RedisRateLimiter:
    """
    Fixed-window rate limiter implemented with Redis counters.
    The Lua script increments the current window's counter and sets its expiry
    atomically, so concurrent requests cannot oversubscribe a window.
    """

    LUA_SCRIPT = r"""
    local key = KEYS[1]
    local window = tonumber(ARGV[1])
    local limit = tonumber(ARGV[2])
    -- Redis server time (seconds)
    local t = redis.call('TIME')
    local now = tonumber(t[1])
    local window_start = now - (now % window)
    local bucket_key = key .. ':' .. window_start
    local current = redis.call('INCR', bucket_key)
    if current == 1 then
        redis.call('EXPIRE', bucket_key, window)
    end
    local reset = window - (now - window_start)
    if current <= limit then
        return {1, limit - current, reset}
    end
    return {0, 0, reset}
    """

    def __init__(self, redis: aioredis.Redis, fail_open: bool = True):
        self.redis = redis
        self.fail_open = fail_open
        self.last_log_time = 0
        self._script_sha = None

    async def _load_script(self) -> None:
        self._script_sha = await self.redis.script_load(self.LUA_SCRIPT)

    async def _execute_script(
        self,
        key: str,
        window_seconds: int,
        limit: int,
    ):
        if self._script_sha is None:
            await self._load_script()

        try:
            return await self.redis.evalsha(
                self._script_sha,
                1,
                key,
                window_seconds,
                limit,
            )

        except aioredis.ResponseError as exc:
            # Redis restarted and lost cached scripts.
            if "NOSCRIPT" not in str(exc):
                raise

            logger.warning("Redis Lua script cache was cleared. Reloading...")

            await self._load_script()

            return await self.redis.evalsha(
                self._script_sha,
                1,
                key,
                window_seconds,
                limit,
            )

    async def allow_request(
        self, 
        key: str, 
        limit: int, 
        window_seconds: int
    ) -> RateLimitResult:
        """
        Attempt to consume a single slot for the given key.
        Returns (allowed: bool, value: int)
          - if allowed == True: value is remaining tokens
          - if allowed == False: value is reset time in seconds
        """
        try:
            result = await self._execute_script(
                key,
                window_seconds,
                limit,
            )

            allowed = bool(result[0])
            value = int(result[1])
            reset = int(result[2])

            if allowed:
                return RateLimitResult(
                    allowed=True,
                    remaining=value,
                    limit=limit,
                    reset_after=reset,
                )

            return RateLimitResult(
                allowed=False,
                remaining=0,
                limit=limit,
                retry_after=reset,
                reset_after=reset,
            )

        except Exception as exc:
            now = time.time()
            if now - self.last_log_time >= 60:
                logger.error("Rate limiter error for key %s: %s", key, exc)
                self.last_log_time = now

            # Fail-open vs fail-closed: default to fail-open for availability

            if self.fail_open:
                return RateLimitResult(
                    allowed=True,
                    remaining=-1,
                    limit=limit,
                )

            # If fail-closed, treat as blocked
            return RateLimitResult(
                allowed=False,
                remaining=0,
                limit=limit,
                retry_after=window_seconds,
            )

def get_client_ip_from_request(request: Request) -> str:
    """
    Extract the real client IP from the request.
    - Check X-Forwarded-For (the left-most entry is the original client)
    - Check X-Real-IP
    - Fall back to request.client.host
    Important: In production ensure your reverse proxy/load-balancer sets these headers and that
    FastAPI/Uvicorn is configured to trust the proxy (or use ProxyHeaders middleware if needed).
    """
    # Prefer X-Forwarded-For (may contain comma separated list)
    xff = request.headers.get("X-Forwarded-For") or request.headers.get("x-forwarded-for")
    if xff:
        # left-most IP is the original client
        return xff.split(",")[0].strip()

    # Next, X-Real-IP
    xr = request.headers.get("X-Real-IP") or request.headers.get("x-real-ip")
    if xr:
        return xr.strip()

    # Fallback to ASGI client
    if request.client:
        return request.client.host

    return "127.0.0.1"

__all__ = [
    "RedisRateLimiter",
    "RateLimitConfig",
    "RateLimitResult",
    "ANALYZE_RATE_LIMIT",
    "PUBLIC_RATE_LIMIT",
    "get_client_ip_from_request",
]