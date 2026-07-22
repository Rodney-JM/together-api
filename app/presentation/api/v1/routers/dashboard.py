from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as aioredis

from app.application.schemas.dashboard import DashboardResponse
from app.application.services.domain_services.dashboard_service import DashboardService
from app.core.dependencies.auth import require_couple
from app.core.dependencies.rate_limit import RateLimit
from app.domain.models.user import User
from app.infra.db.session import get_db_session
from app.infra.cache.client import get_redis

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

CoupleUser = Annotated[User, Depends(require_couple)]


@router.get("", response_model=DashboardResponse)
async def get_dashboard(
    user: CoupleUser,
    _: RateLimit,
    db: AsyncSession = Depends(get_db_session),
    redis: aioredis.Redis = Depends(get_redis),
) -> DashboardResponse:
    service = DashboardService(db, redis)
    return await service.build(user)
