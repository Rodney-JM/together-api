import json
from collections.abc import AsyncGenerator

import redis.asyncio as aioredis

from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)

_pool: aioredis.ConnectionPool | None = None

def get_redis_pool() -> aioredis.ConnectionPool:
    global _pool
    if _pool is None:
        _pool = aioredis.ConnectionPool.from_url(
            settings.REDIS_URL,
            max_connections=50,
            decode_responses=True
        )
    return _pool

async def get_redis() -> AsyncGenerator[aioredis.Redis, None]:
    client = aioredis.Redis(connection_pool=get_redis_pool())
    
    try:
        yield client
    finally:
        await client.aclose()

#key-builders

def _key_mood(user_id: str) -> str:
    return f"mood:{user_id}"

def _key_online(user_id: str) -> str:
    return f"online:{user_id}"

def _key_watch_state(couple_id: str) -> str:
    return f"watch_state:{couple_id}"

def _key_night_state(couple_id: str) -> str:
    return f"night_state:{couple_id}"

def _k_premium(uid: str) -> str:
    return f"premium: {uid}"

def _key_cache(namespace: str, key: str) -> str:
    return f"cache:{namespace}:{key}"