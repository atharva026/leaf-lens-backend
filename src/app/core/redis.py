import redis.asyncio as aioredis
from src.app.core.config import config
from src.app.core.logging import get_logger

logger = get_logger(__name__)

# Global variable to hold the Redis connection pool
_redis_pool: aioredis.ConnectionPool | None = None

async def redis_on_startup() -> None:
    """Initialize the Redis connection pool on application startup."""
    global _redis_pool
    
    # Redis pool: use SSLConnection for prod (Upstash requires TLS = rediss://),
    # plain Connection for local Docker (redis://). ConnectionPool() (unlike
    # from_url()) needs connection_class explicitly — it won't auto-detect
    # ssl from a scheme string, and doesn't accept ssl=True as a kwarg.
    # If Upstash throws cert verification errors, add ssl_cert_reqs=None
    # for prod only (kept off by default since it weakens verification).
    connection_class = aioredis.SSLConnection if config.ENVIRONMENT == "prod" else aioredis.Connection

    _redis_pool = aioredis.ConnectionPool(
        connection_class=connection_class,
        host=config.REDIS_CONFIG.redis_host,
        port=config.REDIS_CONFIG.redis_port,
        db=config.REDIS_CONFIG.redis_db,
        username=config.REDIS_CONFIG.redis_username,
        password=config.REDIS_CONFIG.redis_password,
        max_connections=20,
        socket_connect_timeout=5,
        socket_timeout=5,
        retry_on_timeout=True,
        health_check_interval=30,
        decode_responses=True,
        # **({"ssl_cert_reqs": None} if config.ENVIRONMENT == "prod" else {}),
    )

    # Verify connection eagerly — fail loud at startup
    async with aioredis.Redis(connection_pool=_redis_pool) as client:
        await client.ping()

    logger.info(
        "Redis connection pool initialized at %s",
        config.REDIS_CONFIG.redis_host,
    )

async def redis_on_shutdown() -> None:
    """Close the Redis connection pool on application shutdown."""
    global _redis_pool
    if _redis_pool:
        await _redis_pool.aclose()
        _redis_pool = None
        logger.info("Redis connection pool closed")

async def get_redis() -> aioredis.Redis:
    """Get a Redis client instance from the connection pool. Raises an error if the pool is not initialized."""
    if _redis_pool is None:
        raise RuntimeError("Redis pool not initialized")
    return aioredis.Redis(connection_pool=_redis_pool)
