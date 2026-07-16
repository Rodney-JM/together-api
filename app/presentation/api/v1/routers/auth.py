from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as aioredis
import secrets
import string
from datetime import datetime, timezone, timedelta

from app.application.schemas.user import (
    UserRegister,
    UserLogin,
    TokenResponse,
    RefreshRequest,
    UserResponse,
)
from app.application.schemas.couple import (
    CoupleInviteResponse,
    JoinCoupleRequest,
    CoupleResponse,
    PartnerPublicResponse,
)
from app.application.services.auth_service import AuthService
from app.application.services.couple_service import CoupleService
from app.core.dependencies.auth import get_current_user, require_couple
from app.core.dependencies.rate_limit import AuthRateLimit
from app.core.dependencies.auth import DBSession
from app.core.security import create_access_token
from app.core.config import settings
from app.domain.models.user import User
from app.infra.cache.premium_cache import PremiumCache
from app.infra.db.session import get_db_session
from app.infra.cache.client import get_redis
from app.infra.repositories.refresh_tokens_repo import RefreshTokenRepository
from app.infra.repositories.subscription_repo import SubscriptionRepository

auth_router = APIRouter(prefix="/auth", tags=["Auth"])
couple_router = APIRouter(prefix="/couple", tags=["Couple"])

CurrentUser = Annotated[User, Depends(get_current_user)]
CoupleUser = Annotated[User, Depends(require_couple)]


# Auth Routes

@auth_router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    payload: UserRegister,
    request: Request,
    _: AuthRateLimit,
    db: DBSession,
    redis: aioredis.Redis = Depends(get_redis),
) -> TokenResponse:
    service = AuthService(db, redis)
    result = await service.register(
        email=payload.email,
        display_name=payload.name,
        password=payload.password,
        request=request,
    )
    return TokenResponse(**result)


@auth_router.post("/login", response_model=TokenResponse)
async def login(
    payload: UserLogin,
    request: Request,
    _: AuthRateLimit,
    db: DBSession,
    redis: aioredis.Redis = Depends(get_redis),
) -> TokenResponse:
    service = AuthService(db, redis)
    result = await service.login(
        email=payload.email,
        password=payload.password,
        request=request,
    )
    return TokenResponse(**result)


@auth_router.post("/refresh", response_model=TokenResponse)
async def refresh(
    payload: RefreshRequest,
    request: Request,
    db: DBSession,
    redis: aioredis.Redis = Depends(get_redis),
) -> TokenResponse:
    service = AuthService(db, redis)
    result = await service.refresh(
        raw_refresh_token=payload.refresh_token,
        request=request,
    )
    return TokenResponse(**result)


@auth_router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    payload: RefreshRequest,
    db: DBSession,
    redis: aioredis.Redis = Depends(get_redis),
) -> None:
    service = AuthService(db, redis)
    await service.logout(raw_refresh_token=payload.refresh_token)


@auth_router.get("/me", response_model=UserResponse)
async def me(
    user: CurrentUser,
    db: DBSession,
    redis: aioredis.Redis = Depends(get_redis)
) -> UserResponse:
    cache = PremiumCache(redis)
    cached = await cache.get(str(user.id))
    if cached is None:
        sub = await SubscriptionRepository(db).get_by_user(user.id)
        cached = sub.is_premium_active if sub else False
        await cache.set(str(user.id), cached)
    
    resp = UserResponse.model_validate(user)
    resp.is_premium = cached
    return resp


# Couple Routes


@couple_router.post("/invite", response_model=CoupleInviteResponse)
async def invite(
    user: CurrentUser,
    db: DBSession,
) -> CoupleInviteResponse:
    service = CoupleService(db)
    result = await service.create_invite(user)
    return CoupleInviteResponse(**result)


@couple_router.post("/join", response_model=UserResponse)
async def join(
    payload: JoinCoupleRequest,
    user: CurrentUser,
    db: DBSession,
) -> UserResponse:
    service = CoupleService(db)
    updated_user = await service.join_couple(user, payload.invite_code)
    return UserResponse(
        id=str(updated_user.id),
        name=updated_user.name,
        email=updated_user.email,
        avatar_url=updated_user.avatar_url,
        created_at=updated_user.created_at,
    )


@couple_router.get("/me", response_model=CoupleResponse)
async def couple_me(
    user: CoupleUser,
    db: DBSession,
) -> CoupleResponse:
    service = CoupleService(db)
    couple = await service.couples.get_by_id(user.couple_id)
    return CoupleResponse(
        id=couple.id,
        anniversary_date=couple.relationship_start_date,
        current_streak=couple.current_streak,
        longest_streak=couple.longest_streak,
        invite_code=couple.invite_code,
        members=[
            PartnerPublicResponse(
                id=m.id,
                display_name=m.name,
                avatar_url=m.avatar_url,
                current_mood=m.current_mood,
                mood_updated_at=m.mood_updated_at,
            )
            for m in couple.members
        ],
    )