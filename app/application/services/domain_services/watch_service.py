from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.schemas.watch_session import (
    WatchSessionCreateRequest,
    WatchSessionResponse,
)
from app.core.exceptions import (
    ForbiddenError,
    NotFoundError,
    CoupleRequiredError,
    BusinessRuleError,
)
from app.domain.models.user import User
from app.domain.models.session_models.watch_session import WatchSession
from app.infra.repositories.session_repositories.watch_session_repo import (
    WatchSessionRepository,
)


class WatchService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = WatchSessionRepository(db)

    async def create_session(
        self, user: User, payload: WatchSessionCreateRequest
    ) -> WatchSessionResponse:
        if not user.couple_id:
            raise CoupleRequiredError()

        existing = await self.repo.get_active_for_couple(user.couple_id)
        if existing:
            existing.ended_at = datetime.now(timezone.utc)
            await self.db.flush()

        session = WatchSession(
            couple_id=user.couple_id,
            initiated_by=user.id,
            media_title=payload.media_title,
            media_url=payload.media_url,
            media_type=payload.media_type,
            is_playing=True,
            current_position_seconds=0.0,
        )
        
        session = await self.repo.create(session)
        return self._to_response(session)

    async def get_active(self, user: User) -> WatchSessionResponse | None:
        if not user.couple_id:
            raise CoupleRequiredError()
        session = await self.repo.get_active_for_couple(user.couple_id)
        if not session:
            return None
        return self._to_response(session)

    async def end_session(self, user: User, session_id: UUID) -> None:
        session = await self._get_couple_session(session_id, user)
        session.is_playing = False
        session.ended_at = datetime.now(timezone.utc)
        await self.db.flush()
        
    async def update_position(self, user: User, session_id: UUID, position: float, is_playing: bool) -> WatchSessionResponse:
        # Atualiza a posição do video e o estado de playing
        
        session = await self._get_couple_session(session_id, user)
        
        if session.ended_at is not None:
            raise BusinessRuleError("Sessão de assistir encerrada")
        
        update_data = {
            "current_position_seconds": position,
            "is_playing": is_playing,
        }
        
        updated_session = await self.repo.update(session_id, update_data)
        return self._to_response(updated_session)
    

    async def _get_couple_session(
        self, session_id: UUID, user: User
    ) -> WatchSession:
        if not user.couple_id:
            raise CoupleRequiredError()
        session = await self.repo.get_by_id(session_id)
        if not session:
            raise NotFoundError("Sessao de assistir")
        if session.couple_id != user.couple_id:
            raise ForbiddenError()
        return session

    def _to_response(self, session: WatchSession) -> WatchSessionResponse:
        return WatchSessionResponse(
            id=session.id,
            media_title=session.media_title,
            media_url=session.media_url,
            media_type=session.media_type,
            is_playing=session.is_playing,
            current_position_seconds=float(session.current_position_seconds),
            couple_id=session.couple_id,
            created_at=session.created_at,
        )
