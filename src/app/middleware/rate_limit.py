import time
from dataclasses import dataclass
from typing import Literal

from starlette import status
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp, Receive, Scope, Send, Message

from src.app.core.rate_limiter import (
    ANALYZE_RATE_LIMIT,
    PUBLIC_RATE_LIMIT,
    RedisRateLimiter,
    RateLimitResult,
    get_client_ip_from_request,
)

IpKeyPrefix = Literal["analyze", "public"]

SKIP_RATE_LIMIT_PATHS = frozenset({
    "/",
    "/health",
})

# Data
@dataclass
class RateLimitInfo:
    """Carries rate limit context from the check site to the response headers."""
    limit: int
    remaining: int
    reset_at: int # Unix timestamp (seconds) when the window resets
    retry_after: int | None = None

# Builders
def _build_rate_limit_info(result: RateLimitResult, window_seconds: int) -> RateLimitInfo:
    now = int(time.time())
    reset_after = result.retry_after if not result.allowed else result.reset_after
    reset_at = now + (reset_after if reset_after is not None else window_seconds)
    return RateLimitInfo(
        limit=result.limit,
        remaining=result.remaining,
        reset_at=reset_at,
        retry_after=result.retry_after if not result.allowed else None,
    )

def _rate_limit_headers(info: RateLimitInfo) -> dict[str, str]:
    headers = {
        "X-RateLimit-Limit": str(info.limit),
        "X-RateLimit-Remaining": str(max(info.remaining, 0)),
        "X-RateLimit-Reset": str(info.reset_at),
    }
    if info.retry_after is not None:
        headers["Retry-After"] = str(info.retry_after)
    return headers

def _too_many_requests(info: RateLimitInfo) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "success": False,
            "error": {
                "code": "TOO_MANY_REQUESTS",
                "message": "Too many requests. Please try again in a few seconds.",
                "reset": info.retry_after,
            },
        },
        headers=_rate_limit_headers(info),
    )


# Core rate-limit primitive
async def _check_ip_limit(
    limiter: RedisRateLimiter | None,
    ip: str,
    limit: int,
    window_seconds: int,
    prefix: IpKeyPrefix
) -> RateLimitResult | None:
    if limiter is None:
        return None
    key = f"rl:ip:{prefix}:{ip}"   # e.g. rl:ip:analyze:1.2.3.4 / rl:ip:public:1.2.3.4
    return await limiter.allow_request(key, limit=limit, window_seconds=window_seconds)

async def _enforce_ip_limit(
    limiter: RedisRateLimiter | None,
    ip: str,
    limit: int,
    window_seconds: int,
    prefix: IpKeyPrefix
) -> tuple[bool, RateLimitInfo | None]:
    """
    Run an IP-based rate limit check and return (denied, info).

    Returns:
        (True,  info)  — request was denied; caller should send _too_many_requests(info)
        (False, info)  — request allowed with a live limiter; inject headers
        (False, None)  — no limiter configured; pass through without headers
    """
    result = await _check_ip_limit(limiter, ip, limit, window_seconds, prefix)
    if result is None:
        return False, None
    info = _build_rate_limit_info(result, window_seconds)
    return not result.allowed, info

# ASGI send wrapper
def _inject_headers_into_send(send: Send, extra_headers: dict[str, str]) -> Send:
    """Inject rate-limit headers into http.response.start without buffering the body."""
    async def send_with_headers(message: Message) -> None:
        if message["type"] == "http.response.start":
            existing_headers = list(message.get("headers", []))

            for name, value in extra_headers.items():
                existing_headers.append(
                    (name.encode("latin-1"), value.encode("latin-1"))
                )
            message = {**message, "headers": existing_headers}

        await send(message)
    return send_with_headers

def _patched_send(send: Send, info: RateLimitInfo | None) -> Send:
    """Return a header-injecting send when we have rate-limit info, raw send otherwise."""
    if info is None:
        return send
    return _inject_headers_into_send(send, _rate_limit_headers(info))

# Middleware
class RateLimitMiddleware:
    """
    Pure ASGI rate-limiting middleware.

    Fixed-window, IP-based rate limiting with no authentication dependency.
    Analyze endpoints use the stricter analyze bucket; all other API traffic
    uses the public bucket.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope) #, receive, send) # no receive/send

        if request.method == "OPTIONS":
            await self.app(scope, receive, send)
            return

        if "state" not in scope:
            scope["state"] = {}

        limiter: RedisRateLimiter | None = getattr(request.app.state, "rate_limiter", None)
        ip = get_client_ip_from_request(request)

        response = await self._route(scope, limiter, ip, send)

        if response is not None:
            await response(scope, receive, send)
        else:
            patched_send = scope["state"].pop("rate_limit_send_patch", send)
            await self.app(scope, receive, patched_send)

    async def _route(
        self,
        scope: Scope,
        limiter: RedisRateLimiter | None,
        ip: str,
        send: Send,
    ) -> Response | None:
        """
        Determine the correct rate-limit action for this request.
        Returns a Response to short-circuit (429 / 401), or None to continue
        """
        if scope["path"] in SKIP_RATE_LIMIT_PATHS:   # early exit, zero Redis calls
            return None

        is_analyze = scope["path"].startswith("/api/v1/analyze")
        rate_limit = ANALYZE_RATE_LIMIT if is_analyze else PUBLIC_RATE_LIMIT
        prefix: IpKeyPrefix = "analyze" if is_analyze else "public"
        return await self._handle_ip_limited(
            scope,
            send,
            limiter,
            ip,
            rate_limit.limit,
            rate_limit.window_seconds,
            prefix,
        )

    async def _handle_ip_limited(
        self,
        scope: Scope,
        send: Send,
        limiter: RedisRateLimiter | None,
        ip: str,
        limit: int,
        window_seconds: int,
        prefix: IpKeyPrefix,
    ) -> Response | None:
        """Apply an IP-based limit; inject headers on success, 429 on denial."""
        denied, info = await _enforce_ip_limit(limiter, ip, limit, window_seconds, prefix)
        if denied:
            return _too_many_requests(info)

        # Store a real callable, wrapping the live send
        scope["state"]["rate_limit_send_patch"] = _patched_send(send, info)

        return None
