import json
from datetime import date, timezone
from datetime import datetime

import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.schemas.couple import PartnerPublicResponse
from app.application.schemas.dashboard import DashboardResponse
from app.application.schemas.memory import MemoryResponse
from app.application.schemas.special_dates import SpecialDateResponse
from app.domain.models.user import User
from app.infra.cache.client import _key_cache
from app.infra.cache.premium_cache import PremiumCache
from app.infra.cache.presence import PresenceService
from app.infra.repositories.couple_repo import CoupleRepository
from app.infra.repositories.memory_repo import MemoryRepository
from app.infra.repositories.session_repositories.ritual_entry_repo import (
    RitualEntryRepository,
)
from app.infra.repositories.session_repositories.ritual_repo import RitualRepository
from app.infra.repositories.session_repositories.special_date_repo import (
    SpecialDateRepository,
)
from app.infra.repositories.subscription_repo import SubscriptionRepository
from app.infra.repositories.user_repo import UserRepository
from app.infra.storage.storage_service import get_presigned_url


class DashboardService:
    def __init__(self, db: AsyncSession, redis: aioredis.Redis | None = None) -> None:
        self.db = db
        self.user_repo = UserRepository(db)
        self.couple_repo = CoupleRepository(db)
        self.special_date_repo = SpecialDateRepository(db)
        self.ritual_repo = RitualRepository(db)
        self.ritual_entry_repo = RitualEntryRepository(db)
        self.memory_repo = MemoryRepository(db)
        self.sub_repo = SubscriptionRepository(db)
        self.premium_cache = PremiumCache(redis) if redis else None
        self.presence = PresenceService(redis) if redis else None
        self.redis = redis

    async def build(self, user: User) -> DashboardResponse:
        if self.redis:
            cached = await self.redis.get(_key_cache("dashboard", str(user.id)))
            if cached:
                return DashboardResponse(**json.loads(cached))

        response = await self._build(user)

        if self.redis:
            await self.redis.setex(
                _key_cache("dashboard", str(user.id)), 30, response.model_dump_json()
            )

        return response

    async def _build(self, user: User) -> DashboardResponse:
        my_mood = user.current_mood

        partner = await self._get_partner_data(user)
        couple_streak = await self._get_couple_streak(user)
        next_date = await self._get_next_special_date(user)
        rituals_completed, rituals_total = await self._get_ritual_counts(user)
        recent_photos = await self._get_recent_photos(user)
        is_premium = await self._is_premium(user)

        return DashboardResponse(
            my_mood=my_mood,
            partner=partner,
            couple_streak=couple_streak,
            next_special_date=next_date,
            today_rituals_completed=rituals_completed,
            today_rituals_total=rituals_total,
            recent_photos=recent_photos,
            is_premium_active=is_premium,
        )

    async def _get_partner_data(self, user: User) -> PartnerPublicResponse | None:
        if not user.couple_id:
            return None

        partner = await self.user_repo.get_couple_partner(user)
        if not partner:
            return None

        online = False
        if self.presence:
            online = await self.presence.is_online(str(partner.id))

        return PartnerPublicResponse(
            id=partner.id,
            display_name=partner.name,
            avatar_url=partner.avatar_url,
            current_mood=partner.current_mood,
            mood_updated_at=partner.mood_updated_at,
            is_online=online,
        )

    async def _get_couple_streak(self, user: User) -> int:
        if not user.couple_id:
            return 0
        couple = await self.couple_repo.get_by_id(user.couple_id)
        return couple.current_streak if couple else 0

    async def _get_next_special_date(self, user: User) -> SpecialDateResponse | None:
        if not user.couple_id:
            return None
        date = await self.special_date_repo.get_next_upcoming(user.couple_id)
        if not date:
            return None
        return SpecialDateResponse(
            id=date.id,
            title=date.title,
            icon=date.icon,
            event_date=date.event_date,
            is_recurring_yearly=date.is_recurring_yearly,
            notify_days_before=date.notify_days_before,
            notes=date.notes,
            created_at=date.created_at,
        )

    async def _get_ritual_counts(self, user: User) -> tuple[int, int]:
        if not user.couple_id:
            return 0, 0

        active = await self.ritual_repo.get_active_by_couple(user.couple_id)
        total = len(active)

        if total == 0:
            return 0, 0

        today = datetime.now(timezone.utc)
        completed = await self.ritual_entry_repo.count_today_completed_for_couple(
            user.couple_id, today
        )
        return completed, total

    async def _get_recent_photos(self, user: User) -> list[MemoryResponse]:
        if not user.couple_id:
            return []

        memories = await self.memory_repo.get_recent_by_couple(user.couple_id, limit=6)
        return [self._to_memory_response(m) for m in memories]

    async def _is_premium(self, user: User) -> bool:
        if self.premium_cache:
            cached = await self.premium_cache.get(str(user.id))
            if cached is not None:
                return cached

        sub = await self.sub_repo.get_by_user(user.id)
        result = sub.is_premium_active if sub else False

        if self.premium_cache:
            await self.premium_cache.set(str(user.id), result)

        return result

    def _to_memory_response(self, memory) -> MemoryResponse:
        return MemoryResponse(
            id=str(memory.id),
            album_id=str(memory.album_id),
            author_id=str(memory.author_id),
            title=memory.caption or "",
            note=memory.caption,
            memory_date=memory.memory_date,
            media_url=get_presigned_url(memory.s3_key) if memory.s3_key else None,
            thumbnail_url=get_presigned_url(memory.s3_thumbnail_key) if memory.s3_thumbnail_key else None,
            media_type=memory.media_type,
            created_at=memory.created_at,
            updated_at=memory.updated_at,
        )
