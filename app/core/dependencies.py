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
from app.infra.cache.client import 