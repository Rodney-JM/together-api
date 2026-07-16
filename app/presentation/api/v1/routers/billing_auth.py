import json
from fastapi import APIRouter, Depends
from redis.asyncio import Redis

from app.application.schemas.billing import (
    CheckoutSessionRequest,
    CheckoutSessionResponse,
    CustomerPortalResponse,
    SubscriptionResponse,
)
from app.application.services.subscription_service.subscription_service import SubscriptionService
from app.core.dependencies.auth import DBSession, CurrentUser
from app.infra.cache.client import get_redis

router = APIRouter(prefix="/billing", tags=["Billing - Authenticated"])

_SUB_CACHE_PREFIX = "sub_cache:"
_SUB_CACHE_TTL = 120


def _sub_cache_key(user_id: str) -> str:
    return f"{_SUB_CACHE_PREFIX}{user_id}"


@router.get("/me", response_model=SubscriptionResponse | None)
async def get_my_subscription(
    current_user: CurrentUser,
    db: DBSession,
    redis: Redis = Depends(get_redis),
):
    cache_key = _sub_cache_key(str(current_user.id))
    cached = await redis.get(cache_key)
    if cached is not None:
        return SubscriptionResponse.model_validate(json.loads(cached))

    service = SubscriptionService(db, redis)
    sub = await service.get_my_subscription(current_user)
    if sub is not None:
        await redis.setex(cache_key, _SUB_CACHE_TTL, sub.model_dump_json())
    return sub


@router.post("/checkout", response_model=CheckoutSessionResponse)
async def create_checkout_session(
    body: CheckoutSessionRequest,
    current_user: CurrentUser,
    db: DBSession,
    redis: Redis = Depends(get_redis),
):
    service = SubscriptionService(db, redis)
    return await service.create_checkout_session(current_user, body.billing_interval)


@router.post("/portal", response_model=CustomerPortalResponse)
async def create_customer_portal(
    current_user: CurrentUser,
    db: DBSession,
    redis: Redis = Depends(get_redis),
):
    service = SubscriptionService(db, redis)
    return await service.get_customer_portal(current_user)
