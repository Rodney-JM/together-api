import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.schemas.mood import (
    MoodUpdateRequest,
    MoodResponse,
)
from app.core.exceptions import (
    CoupleRequiredError,
    NotFoundError,
)
from app.domain.models.user import User
from app.infra.repositories.user_repo import UserRepository
from app.infra.cache.mood import MoodCache


class MoodService:
    def __init__(self, db: AsyncSession, redis: aioredis.Redis | None = None) -> None:
        self.db = db
        self.user_repo = UserRepository(db)
        self.mood_cache = MoodCache(redis) if redis else None

    async def update(self, user: User, payload: MoodUpdateRequest, ws_manager) -> MoodResponse:
        user = await self.user_repo.update_mood(user, payload.mood)

        if self.mood_cache:
            await self.mood_cache.set(str(user.id), user.current_mood.value)

        if user.couple_id:
            await ws_manager.broadcast_to_couple(
                str(user.couple_id),
                {"type": "mood_update", "user_id": str(user.id), "mood": payload.mood.value, "updated_at": user.mood_updated_at.isoformat()},
            )
        return MoodResponse(
            user_id=user.id,
            mood=user.current_mood,
            updated_at=user.mood_updated_at,
        )

    async def get_partner_mood(self, user: User) -> MoodResponse:
        if not user.couple_id:
            raise CoupleRequiredError()

        partner = await self.user_repo.get_couple_partner(user)
        if not partner:
            raise NotFoundError("Parceiro(a)")

        if self.mood_cache and partner.current_mood:
            await self.mood_cache.set(str(partner.id), partner.current_mood.value)

        return MoodResponse(
            user_id=partner.id,
            mood=partner.current_mood,
            updated_at=partner.mood_updated_at,
        )
