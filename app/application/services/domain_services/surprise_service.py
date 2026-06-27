from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.application.schemas.surprises import SurpriseCreateRequest, SurpriseResponse
from app.application.schemas.common import PaginatedResponse
from app.core.exceptions import (
    ForbiddenError,
    NotFoundError,
    SubscriptionLimitError,
    CoupleRequiredError,
    SurpriseLockError,
)
from app.domain.models.user import User
from app.domain.models.session_models.surprise import Surprise, SurpriseStatus
from app.infra.repositories.session_repositories.surprise_repo import SurpriseRepository
from app.application.services.domain_services.helpers import _get_plan, _get_partner
from app.infra.storage.storage_service import get_presigned_url


class SurpriseService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = SurpriseRepository(db)

    async def create(
        self, user: User, payload: SurpriseCreateRequest
    ) -> SurpriseResponse:
        if not user.couple_id:
            raise CoupleRequiredError()

        plan = await _get_plan(user, self.db)
        if plan and not plan.can_send_surprises:
            raise SubscriptionLimitError(
                "Seu plano não permite enviar surpresas. Faça o upgrade para o Premium."
            )

        partner = await _get_partner(user, self.db)
        if not partner:
            raise CoupleRequiredError("Você precisa de um parceiro vinculado para enviar surpresas.")

        now = datetime.now(timezone.utc)

        if payload.unlocks_at and payload.unlocks_at > now:
            status = SurpriseStatus.LOCKED
        else:
            status = SurpriseStatus.DELIVERED

        surprise = Surprise(
            couple_id=user.couple_id,
            sender_id=user.id,
            recipient_id=partner.id,
            title=payload.title,
            message=payload.message,
            surprise_type=payload.surprise_type,
            status=status,
            unlocks_at=payload.unlocks_at,
            opened_at=None,
        )

        self.db.add(surprise)
        await self.db.flush()

        return self._to_response(surprise, user)

    async def open_surprise(self, user: User, surprise_id: UUID) -> SurpriseResponse:
        surprise = await self.db.get(Surprise, surprise_id)
        if not surprise:
            raise NotFoundError("Surpresa")
        if surprise.couple_id != user.couple_id:
            raise ForbiddenError("Você não tem permissão para acessar esta surpresa.")
        if surprise.recipient_id != user.id:
            raise ForbiddenError("Apenas o destinatário pode abrir esta surpresa.")

        if surprise.status == SurpriseStatus.OPENED:
            return self._to_response(surprise)

        if surprise.status == SurpriseStatus.LOCKED:
            now = datetime.now(timezone.utc)
            if not surprise.unlocks_at or surprise.unlocks_at > now:
                raise SurpriseLockError()
            surprise.status = SurpriseStatus.DELIVERED

        if surprise.status != SurpriseStatus.DELIVERED:
            raise ForbiddenError("Esta surpresa não pode ser aberta no estado atual.")

        surprise.status = SurpriseStatus.OPENED
        surprise.opened_at = datetime.now(timezone.utc)

        await self.db.flush()

        return self._to_response(surprise, user)

    async def get_surprise(self, user: User, surprise_id: UUID) -> SurpriseResponse:
        surprise = await self.db.get(Surprise, surprise_id)
        if not surprise:
            raise NotFoundError("Surpresa")
        if surprise.couple_id != user.couple_id:
            raise ForbiddenError()

        return self._to_response(surprise, user)

    async def list_surprises(
        self,
        user: User,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse[SurpriseResponse]:
        if not user.couple_id:
            raise CoupleRequiredError()

        offset = (page - 1) * page_size
        items, total = await self.repo.get_for_couple(
            couple_id=user.couple_id,
            limit=page_size,
            offset=offset,
        )

        return PaginatedResponse(
            items=[self._to_response(s, user) for s in items],
            total=total,
            page=page,
            page_size=page_size,
            has_next=(offset + len(items)) < total,
        )

    async def delete_surprise(self, user: User, surprise_id: UUID) -> None:
        surprise = await self.db.get(Surprise, surprise_id)
        if not surprise:
            raise NotFoundError("Surpresa")
        if surprise.sender_id != user.id:
            raise ForbiddenError("Apenas o remetente pode excluir esta surpresa.")
        if surprise.status == SurpriseStatus.OPENED:
            raise ForbiddenError("Não é possível excluir uma surpresa já aberta.")

        await self.db.delete(surprise)
        await self.db.flush()

    def _to_response(self, surprise: Surprise, current_user: User) -> SurpriseResponse:
        url = get_presigned_url(surprise.media_s3_key) if surprise.media_s3_key else None
        
        is_sender = current_user.id == surprise.sender_id
        is_locked = surprise.status == SurpriseStatus.LOCKED
        
        if is_sender or not is_locked:
            message_content = surprise.message
        else:
            message_content = "Está mensagem está trancada!"
        
        return SurpriseResponse(
            id=surprise.id,
            title=surprise.title,
            message=message_content,
            surprise_type=surprise.surprise_type,
            status=surprise.status,
            unlocks_at=surprise.unlocks_at,
            opened_at=surprise.opened_at,
            sender_id=surprise.sender_id,
            media_s3_key=surprise.media_s3_key,
            media_url=url,
            created_at=surprise.created_at,
        )
