import redis.asyncio as aioredis

from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.models.user import User


from app.infra.repositories.user_repo import UserRepository
from app.infra.repositories.subscription_repo import SubscriptionRepository
from app.infra.cache.premium_cache import PremiumCache

async def _get_partner(user: User, db: AsyncSession) -> User | None:
    return await UserRepository(db).get_couple_partner(user)


async def _is_premium(user: User, db: AsyncSession, redis: aioredis.Redis) -> bool:
    cache = PremiumCache(redis)
    cached = await cache.get(str(user.id))
    if cached is not None:
        return cached
    sub = await SubscriptionRepository(db).get_by_user(user.id)
    result = sub.is_premium_active if sub else False
    await cache.set(str(user.id), result)
    return result


async def _get_plan(user: User, db: AsyncSession):
    sub = await SubscriptionRepository(db).get_by_user(user.id)
    return sub.plan if sub else None