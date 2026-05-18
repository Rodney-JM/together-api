from typing import Annotated
from uuid import UUID
from fastapi import Depends, Header, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import Settings
from app.core.exceptions import (
    CoupleRequiredError,
    ForbiddenError,
    RateLimitError,
    UnauthorizedError,
    PremiumRequiredError,
    SubscriptionLimitError
)
from app.core.security import verify_token

from app.domain.enums.plan_tier import PlanTier
from app.domain.models.plan import Plan
from app.domain.models.user import User
from app.infra.cache.client import get_redis
from app.infra.cache.premium_cache import PremiumCache
from app.infra.db.session import get_db_session
from app.infra.repositories.subscription_repo import SubscriptionRepository
from app.infra.repositories.user_repo import UserRepository

bearer = HTTPBearer(auto_error=False)

DBSession = Annotated[object, Depends(get_db_session)]

