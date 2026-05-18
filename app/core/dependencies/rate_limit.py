import redis.asyncio as aioredis
from typing import Annotated

from app.core.config import settings
from fastapi import Request, Depends
from app.core.exceptions import RateLimitError
from app.infra.cache.client import get_redis

async def _rate_limit(request: Request, redis: aioredis.Redis, limit: int) -> None:
    ip = request.client.host if request.client else "unknown"
    key = f"rl:{ip}:{request.url.path}"
    count = await redis.incr(key)
    if count == 1:
        await redis.expire(key, 60)
    if count > limit:
        raise RateLimitError()

async def check_rate_limit(
    request: Request, redis: aioredis.Redis = Depends(get_redis)
) -> None:
    await _rate_limit(request, redis, settings.RATE_LIMIT_PER_MINUTE)

async def check_auth_rate_limit(
    request: Request, redis: aioredis.Redis = Depends(get_redis)
) -> None:
    await _rate_limit(request, redis, settings.RATE_LIMIT_AUTH_PER_MINUTE)

RateLimit = Annotated[None, Depends(check_rate_limit)]
AuthRateLimit = Annotated[None, Depends(check_auth_rate_limit)]