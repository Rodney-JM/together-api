from fastapi import APIRouter, Depends
from redis.asyncio import Redis

from app.application.schemas.billing import PlanResponse, PublicKeyResponse
from app.application.services.subscription_service.subscription_service import SubscriptionService
from app.core.config import settings
from app.core.dependencies.auth import DBSession
from app.infra.cache.client import get_redis

router = APIRouter(prefix="/billing", tags=["Billing - Public"])


@router.get("/plans", response_model=list[PlanResponse])
async def list_plans(db: DBSession, redis: Redis = Depends(get_redis)):
    service = SubscriptionService(db, redis)
    return await service.get_plans()


@router.get("/stripe_key", response_model=PublicKeyResponse)
async def get_stripe_public_key():
    return PublicKeyResponse(publishable_key=settings.STRIPE_PUBLISHABLE_KEY)
