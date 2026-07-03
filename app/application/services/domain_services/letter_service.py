from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.schemas.letter import LetterCreateRequest, LetterResponse
from app.application.schemas.common import PaginatedResponse
from app.core.exceptions import (
    ForbiddenError,
    NotFoundError,
    CoupleRequiredError,
    BusinessRuleError,
)
from app.domain.models.user import User
from app.domain.models.session_models.letter import Letter
from app.domain.enums.letter_status import LetterStatus
from app.infra.repositories.session_repositories.letter_repo import LetterRepository
from app.application.services.domain_services.helpers import _get_partner


class LetterService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = LetterRepository(db)

    async def create_draft(self, user: User, payload: LetterCreateRequest) -> LetterResponse:
        if not user.couple_id:
            raise CoupleRequiredError()

        partner = await _get_partner(user, self.db)
        if not partner:
            raise CoupleRequiredError()

        letter = Letter(
            couple_id=user.couple_id,
            author_id=user.id,
            recipient_id=partner.id,
            body=payload.body,
            status=LetterStatus.DRAFT,
        )
        self.db.add(letter)
        await self.db.flush()

        return self._to_response(letter)

    async def send(self, user: User, letter_id: UUID) -> LetterResponse:
        letter = await self._get_authored(letter_id, user)

        if letter.status != LetterStatus.DRAFT:
            raise BusinessRuleError("Apenas cartas em rascunho podem ser enviadas.")

        letter.status = LetterStatus.SENT
        letter.sent_at = datetime.now(timezone.utc)
        await self.db.flush()

        return self._to_response(letter)

    async def mark_read(self, user: User, letter_id: UUID) -> LetterResponse:
        letter = await self.db.get(Letter, letter_id)
        if not letter:
            raise NotFoundError("Carta")
        if letter.couple_id != user.couple_id:
            raise ForbiddenError()
        if letter.recipient_id != user.id:
            raise ForbiddenError("Apenas o destinatário pode marcar esta carta como lida.")
        if letter.status != LetterStatus.SENT:
            raise BusinessRuleError("Apenas cartas enviadas podem ser marcadas como lidas.")

        letter.status = LetterStatus.READ
        letter.read_at = datetime.now(timezone.utc)
        await self.db.flush()

        return self._to_response(letter)

    async def list(
        self,
        user: User,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse[LetterResponse]:
        if not user.couple_id:
            raise CoupleRequiredError()

        offset = (page - 1) * page_size
        items, total = await self.repo.get_for_couple(
            couple_id=user.couple_id,
            user_id=user.id,
            limit=page_size,
            offset=offset,
        )

        return PaginatedResponse(
            items=[self._to_response(l) for l in items],
            total=total,
            page=page,
            page_size=page_size,
            has_next=(offset + len(items)) < total,
        )

    async def delete(self, user: User, letter_id: UUID) -> None:
        letter = await self._get_authored(letter_id, user)

        if letter.status != LetterStatus.DRAFT:
            raise BusinessRuleError("Apenas cartas em rascunho podem ser excluídas.")

        await self.db.delete(letter)
        await self.db.flush()

    async def _get_authored(self, letter_id: UUID, user: User) -> Letter:
        letter = await self.repo.get_by_id(letter_id)
        if not letter:
            raise NotFoundError("Carta")
        if letter.author_id != user.id:
            raise ForbiddenError()
        return letter

    def _to_response(self, letter: Letter) -> LetterResponse:
        return LetterResponse(
            id=letter.id,
            body=letter.body,
            status=letter.status,
            author_id=letter.author_id,
            recipient_id=letter.recipient_id,
            sent_at=letter.sent_at,
            read_at=letter.read_at,
            created_at=letter.created_at,
        )
