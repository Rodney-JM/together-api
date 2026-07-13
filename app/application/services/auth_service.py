from __future__ import annotations

import secrets
from datetime import datetime, timezone, timedelta
from uuid import UUID

import redis.asyncio as aioredis
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.subscription_service.plan_seeders import assign_free_plan
from app.core.config import settings
from app.core.exceptions import (
    ConflictError,
    InvalidCredentialsError,
    InvalidTokenError
)

from app.core.security import (
    create_access_token,
    hash_password,
    verify_password
)

from app.domain.models.couple_models.audit_log import AuditLog
from app.domain.models.user import User
from app.infra.repositories.refresh_tokens_repo import RefreshTokenRepository
from app.infra.repositories.user_repo import UserRepository
from app.core.logging_config import get_logger

logger = get_logger(__name__)

class AuthService:
    def __init__(self, db: AsyncSession, redis: aioredis.Redis) -> None:
        self.db = db
        self.redis = redis
        self.users = UserRepository(db)
        self.tokens = RefreshTokenRepository(db)
        
    async def register(self, email: str, display_name: str, password: str, request: Request) -> dict:
        if await self.users.get_by_email(email):
            raise ConflictError("Email já cadastrado")
        
        user = User(
            email=email.lower(),
            display_name=display_name,
            password_hash=hash_password(password)
        )
        
        new_user = await self.users.add(user)
        
        if not new_user:
            new_user = user
            
        await self.db.flush()         

        await assign_free_plan(new_user.id, self.db)
        await self._audit(new_user.id, "user.register", request)
        
        tokens_data = await self._issue_tokens(new_user, request)
        
        await self.db.commit()
        return tokens_data
        
    async def login(self, email: str, password: str, request: Request) -> dict:
        user = await self.users.get_by_email(email)
        if not user or not verify_password(password, user.password_hash):
            raise InvalidCredentialsError()
            
        if not user.is_active:
            raise InvalidCredentialsError(details="Conta desativada")
            
        await self._audit(user.id, "user.login", request)
        tokens_data = await self._issue_tokens(user, request)
        
        await self.db.commit()
        return tokens_data
    
    async def refresh(self, raw_refresh_token: str, request: Request) -> dict:
        record = await self.tokens.get_valid_token(raw_refresh_token)
        if not record:
            raise InvalidTokenError()
            
        record.revoked = True 
        
        user = await self.users.get_by_id(record.user_id)
        if not user or not user.is_active:
            raise InvalidTokenError()
            
        await self._audit(user.id, "token.refresh", request)
        tokens_data = await self._issue_tokens(user, request)
        
        await self.db.commit()
        return tokens_data
    
    async def logout(self, raw_refresh_token: str) -> None:
        record = await self.tokens.get_valid_token(raw_refresh_token)
        if record:
            record.revoked = True
            await self.db.commit()
            
    async def _issue_tokens(self, user: User, request: Request) -> dict:
        raw = secrets.token_urlsafe(48)
        expires = datetime.now(timezone.utc) + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
        
        await self.tokens.create(
            user_id=user.id,
            raw_token=raw,
            expires_at=expires,
            user_agent=request.headers.get("user-agent"),
            ip_address=request.client.host if request.client else None
        )
        
        return {
            "access_token": create_access_token(user.id, couple_id=user.couple_id),
            "refresh_token": raw,
            "token_type": "bearer"
        }
        
    async def _audit(self, user_id: UUID, action: str, request: Request) -> None:
        self.db.add(AuditLog(
            user_id=user_id,
            action=action,
            ip_address=request.client.host if request.client else None
        ))