from fastapi import APIRouter, Depends, Request
from redis.asyncio import Redis

from app.application.services.subscription_service.subscription_service import SubscriptionService
from app.core.dependencies.auth import DBSession
from app.core.exceptions import StripeWebhookError
from app.infra.cache.client import get_redis

router = APIRouter(prefix="/webhooks", tags=["Billing - Webhook"])

_SUB_CACHE_PREFIX = "sub_cache:"


def _sub_cache_key(user_id: str) -> str:
    return f"{_SUB_CACHE_PREFIX}{user_id}"


@router.post("/stripe", status_code=200)
async def stripe_webhook(
    request: Request,
    db: DBSession,
    redis: Redis = Depends(get_redis),
):
    signature = request.headers.get("stripe-signature")
    if not signature:
        raise StripeWebhookError("Missing stripe-signature header")

    payload = await request.body()

    service = SubscriptionService(db, redis)
    result = await service.handle_webhook(payload, signature)

    user_id = result.get("user_id")
    if user_id:
        await redis.delete(_sub_cache_key(str(user_id)))

    return {"received": True}
