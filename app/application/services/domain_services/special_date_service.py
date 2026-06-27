from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.schemas.special_dates import (
    SpecialDateCreateRequest,
    SpecialDateUpdateRequest,
    SpecialDateResponse,
)
from app.core.exceptions import (
    NotFoundError,
    ForbiddenError,
    ConflictError,
    BusinessRuleError,
    CoupleRequiredError
)
from app.domain.models.session_models.special_date import SpecialDate
from app.domain.models.user import User
from app.infra.repositories.session_repositories.special_date_repo import (
    SpecialDateRepository,
)


class SpecialDateService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = SpecialDateRepository(db)

    async def create_special_date(
        self,
        user: User,
        payload: SpecialDateCreateRequest,
    ) -> SpecialDateResponse:
        if not user.couple_id:
            raise CoupleRequiredError(
                "Você precisa estar em um relacionamento para criar datas especiais."
            )

        existing = await self.repo.get_all(filters=[
            SpecialDate.couple_id == user.couple_id,
            SpecialDate.title == payload.title,
        ])
        if existing:
            raise ConflictError(
                "Já existe uma data especial com este título e data no seu relacionamento."
            )

        date = SpecialDate(
            couple_id=user.couple_id,
            created_by=user.id,
            title=payload.title,
            icon=payload.icon,
            event_date=payload.event_date,
            is_recurring_yearly=payload.is_recurring_yearly,
            notify_days_before=payload.notify_days_before,
            notes=payload.notes,
        )
        created = await self.repo.add(date)
        return self._to_response(created)

    async def get_special_date(
        self,
        user: User,
        date_id: UUID,
    ) -> SpecialDateResponse:
        date = await self._get_owned(date_id, user)
        return self._to_response(date)

    async def list_special_dates(
        self,
        user: User,
    ) -> list[SpecialDateResponse]:
        if not user.couple_id:
            return []
        dates = await self.repo.get_by_couple(user.couple_id)
        return [self._to_response(d) for d in dates]

    async def get_next_upcoming(
        self,
        user: User,
    ) -> SpecialDateResponse | None:
        if not user.couple_id:
            return None
        date = await self.repo.get_next_upcoming(user.couple_id)
        if not date:
            return None
        return self._to_response(date)

    async def update_special_date(
        self,
        user: User,
        date_id: UUID,
        payload: SpecialDateUpdateRequest,
    ) -> SpecialDateResponse:
        date = await self._get_owned(date_id, user)

        if payload.title is not None and payload.title != date.title:
            existing = await self.repo.get_all(filters=[
                SpecialDate.couple_id == user.couple_id,
                SpecialDate.title == payload.title,
                SpecialDate.id != date_id,
            ])
            if existing:
                raise ConflictError(
                    "Já existe uma data especial com este título no seu relacionamento."
                )

        update_data = payload.model_dump(exclude_unset=True)
        updated = await self.repo.update(date, update_data)
        return self._to_response(updated)

    async def delete_special_date(
        self,
        user: User,
        date_id: UUID,
    ) -> None:
        date = await self._get_owned(date_id, user)
        await self.repo.delete(date)

    async def _get_owned(self, date_id: UUID, user: User) -> SpecialDate:
        date = await self.repo.get_by_id(date_id)
        if not date:
            raise NotFoundError("Data especial")
        if date.couple_id != user.couple_id:
            raise ForbiddenError()
        return date

    def _to_response(self, date: SpecialDate) -> SpecialDateResponse:
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
