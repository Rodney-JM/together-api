from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.schemas.night_together import (
    NightSessionRequest,
    NightSessionResponse,
)
from app.core.exceptions import (
    ForbiddenError,
    NotFoundError,
    CoupleRequiredError,
    BusinessRuleError,
)
from app.domain.models.user import User
from app.domain.models.session_models.night_session import NightSession
from app.domain.enums.night_session_status import NightSessionStatus
from app.infra.repositories.session_repositories.night_session_repo import (
    NightSessionRepository,
)


class NightService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = NightSessionRepository(db)

    async def start_or_join(
        self, user: User, payload: NightSessionRequest
    ) -> NightSessionResponse:
        if not user.couple_id:
            raise CoupleRequiredError()

        active = await self.repo.get_active_for_couple(user.couple_id)

        if active is None:
            session = NightSession(
                couple_id=user.couple_id,
                user1_id=user.id,
                user1_joined_at=datetime.now(timezone.utc),
                ambient_sound=payload.ambient_sound,
                status=NightSessionStatus.WAITING,
            )
            session = await self.repo.add(session)
            return self._to_response(session)

        if active.user1_id == user.id:
            return self._to_response(active)

        if active.user2_id is not None:
            raise BusinessRuleError("Ambos já estão na sessão.")

        update_data = {
            "user2_id": user.id,
            "user2_joined_at": datetime.now(timezone.utc),
            "status": NightSessionStatus.ACTIVE,
        }
        updated_session = await self.repo.update(active, update_data)
        return self._to_response(updated_session)

    async def end(self, user: User, session_id: UUID) -> NightSessionResponse:
        session = await self._get_couple_session(session_id, user)
        if session.status == NightSessionStatus.ENDED:
            raise BusinessRuleError("Sessão já encerrada.")
        
        update_data = {
            "status": NightSessionStatus.ENDED,
            "ended_at": datetime.now(timezone.utc),
        }
        updated_session = await self.repo.update(session, update_data)
        return self._to_response(updated_session)

    async def get_active(self, user: User) -> NightSessionResponse | None:
        if not user.couple_id:
            raise CoupleRequiredError()
        session = await self.repo.get_active_for_couple(user.couple_id)
        if not session:
            return None
        return self._to_response(session)

    async def _get_couple_session(
        self, session_id: UUID, user: User
    ) -> NightSession:
        if not user.couple_id:
            raise CoupleRequiredError()
        session = await self.repo.get_by_id(session_id)
        if not session:
            raise NotFoundError("Sessão noturna")
        if session.couple_id != user.couple_id:
            raise ForbiddenError()
        return session

    def _to_response(self, session: NightSession) -> NightSessionResponse:
        return NightSessionResponse(
            id=session.id,
            status=session.status,
            ambient_sound=session.ambient_sound,
            user1_id=session.user1_id,
            user1_joined_at=session.user1_joined_at,
            user2_id=session.user2_id,
            user2_joined_at=session.user2_joined_at,
            ended_at=session.ended_at,
            created_at=session.created_at,
        )
