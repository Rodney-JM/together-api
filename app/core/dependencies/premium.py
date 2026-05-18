import redis.asyncio as aioredis

from typing import Annotated

from fastapi import Depends
from app.core.dependencies.auth import CurrentUser
from app.core.exceptions import PremiumRequiredError

from app.domain.models.user import User
from app.infra.cache.premium_cache import PremiumCache
from app.infra.repositories.subscription_repo import SubscriptionRepository
from app.infra.db.session import get_db_session
from app.infra.cache.client import get_redis

async def _resolve_is_premium(user: User, db, redis: aioredis.Redis) -> bool:
    cache = PremiumCache(redis)
    cached = await cache.get(str(user.id))
    if cached is not None:
        return cached
    
    sub_repo = SubscriptionRepository(db)
    sub = await sub_repo.get_by_user(user.id)
    is_premium = sub.is_premium_active if sub else False
    await cache.set(str(user.id), is_premium)
    return is_premium

async def require_premium(
    current_user: CurrentUser,
    db=Depends(get_db_session),
    redis: aioredis.Redis = Depends(get_redis)
) -> User:
    if not await _resolve_is_premium(current_user, db, redis):
        raise PremiumRequiredError()
    return current_user

PremiumUser = Annotated[User, Depends(require_premium)]