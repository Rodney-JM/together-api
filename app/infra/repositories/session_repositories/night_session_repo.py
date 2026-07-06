from uuid import UUID
from typing import Any

from sqlalchemy import select
from app.domain.models.session_models.night_session import NightSession
from app.infra.repositories.base import BaseRepository


class NightSessionRepository(BaseRepository[NightSession]):
    model = NightSession

    async def update(self, session_model: NightSession, update_data: dict[str, Any]) -> NightSession:
        for key, value in update_data.items():
            if hasattr(session_model, key):
                setattr(session_model, key, value)
        
        await self.db.flush()
        await self.db.refresh(session_model)
        return session_model
    async def get_active_for_couple(self, couple_id: UUID) -> NightSession | None:
        result = await self.session.execute(
            select(NightSession).where(
                NightSession.couple_id == couple_id,
                NightSession.ended_at == None,
            ).order_by(NightSession.created_at.desc()).limit(1)
        )
        return result.scalar_one_or_none()
