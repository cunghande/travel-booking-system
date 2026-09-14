# ============================================================
# Travel Booking System — Redis Client
# ============================================================

from __future__ import annotations

from collections.abc import AsyncGenerator

import redis.asyncio as aioredis

from app.core.config import settings

# Redis connection pool (singleton)
redis_pool: aioredis.ConnectionPool | None = None


def get_redis_pool() -> aioredis.ConnectionPool:
    """Get or create the Redis connection pool."""
    global redis_pool
    if redis_pool is None:
        redis_pool = aioredis.ConnectionPool.from_url(
            settings.REDIS_URL,
            max_connections=20,
            decode_responses=True,
        )
    return redis_pool


async def get_redis() -> AsyncGenerator[aioredis.Redis, None]:
    """Dependency that yields an async Redis client."""
    pool = get_redis_pool()
    client = aioredis.Redis(connection_pool=pool)
    try:
        yield client
    finally:
        await client.aclose()


async def close_redis_pool() -> None:
    """Close the Redis connection pool on shutdown."""
    global redis_pool
    if redis_pool is not None:
        await redis_pool.aclose()
        redis_pool = None
