from uuid import UUID
from datetime import date, datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.application.schemas.rituals import (
    RitualCreateRequest,
    RitualUpdateRequest,
    RitualResponse,
    RitualEntryRequest,
    RitualWithStatusResponse,
)
from app.application.schemas.common import PaginatedResponse
from app.core.exceptions import (
    ForbiddenError,
    NotFoundError,
    CoupleRequiredError,
    SubscriptionLimitError,
)
from app.core.dependencies.plans import get_user_plan
from app.domain.models.ritual import Ritual, RitualEntry
from app.domain.models.user import User
from app.domain.enums.ritual_status import RitualStatus


class RitualService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_ritual(self, user: User, payload: RitualCreateRequest) -> RitualResponse:
        if not user.couple_id:
            raise CoupleRequiredError()

        plan = await get_user_plan(user, self.db)
        if plan and plan.max_rituals is not None:
            r = await self.db.execute(
                select(func.count()).select_from(Ritual).where(
                    Ritual.couple_id == user.couple_id,
                    Ritual.is_active == True,
                )
            )
            count = r.scalar_one()
            if count >= plan.max_rituals:
                raise SubscriptionLimitError(
                    f"Limite de {plan.max_rituals} rituais ativos atingido. "
                    "Faça upgrade para criar rituais ilimitados."
                )

        new_ritual = Ritual(
            couple_id=user.couple_id,
            created_by=user.id,
            title=payload.title,
            description=payload.description or "",
            icon=payload.icon,
            is_active=True,
            current_streak=0,
            longest_streak=0,
        )
        self.db.add(new_ritual)
        await self.db.flush()
        await self.db.refresh(new_ritual)

        return self._to_response(new_ritual)

    async def list_rituals(
        self, user: User, *, only_active: bool = True, page: int = 1, page_size: int = 30
    ) -> PaginatedResponse[RitualResponse]:
        if not user.couple_id:
            raise CoupleRequiredError()

        filters = [Ritual.couple_id == user.couple_id]
        if only_active:
            filters.append(Ritual.is_active == True)

        offset = (page - 1) * page_size
        r = await self.db.execute(
            select(Ritual)
            .where(*filters)
            .order_by(Ritual.created_at.desc())
            .limit(page_size)
            .offset(offset)
        )
        items = list(r.scalars().all())

        total_r = await self.db.execute(
            select(func.count()).select_from(Ritual).where(*filters)
        )
        total = total_r.scalar_one()

        return PaginatedResponse(
            items=[self._to_response(rit) for rit in items],
            total=total,
            page=page,
            page_size=page_size,
            has_next=(offset + len(items)) < total,
        )

    async def get_ritual(self, user: User, ritual_id: UUID) -> RitualResponse:
        ritual = await self._get_owned(ritual_id, user)
        return self._to_response(ritual)

    async def get_ritual_with_today_status(
        self, user: User, ritual_id: UUID
    ) -> RitualWithStatusResponse:
        if not user.couple_id:
            raise CoupleRequiredError()

        ritual = await self._get_owned(ritual_id, user)

        partner = await self._get_partner(user)

        today = date.today()
        my_entry = await self._get_entry(ritual_id, user.id, today)
        partner_entry = await self._get_entry(ritual_id, partner.id, today) if partner else None

        return RitualWithStatusResponse(
            ritual=self._to_response(ritual),
            my_status=my_entry.status if my_entry else None,
            partner_status=partner_entry.status if partner_entry else None,
        )

    async def update_ritual(
        self, user: User, ritual_id: UUID, payload: RitualUpdateRequest
    ) -> RitualResponse:
        ritual = await self._get_owned(ritual_id, user)

        if payload.title is not None:
            ritual.title = payload.title
        if payload.description is not None:
            ritual.description = payload.description
        if payload.icon is not None:
            ritual.icon = payload.icon
        if payload.is_active is not None:
            ritual.is_active = payload.is_active

        await self.db.flush()
        await self.db.refresh(ritual)
        return self._to_response(ritual)

    async def delete_ritual(self, user: User, ritual_id: UUID) -> None:
        ritual = await self._get_owned(ritual_id, user)
        await self.db.delete(ritual)
        await self.db.flush()

    async def record_entry(
        self, user: User, ritual_id: UUID, payload: RitualEntryRequest
    ) -> RitualWithStatusResponse:
        if not user.couple_id:
            raise CoupleRequiredError()

        ritual = await self._get_owned(ritual_id, user)

        today = date.today()
        existing = await self._get_entry(ritual_id, user.id, today)

        if existing:
            existing.status = payload.status
            if payload.note is not None:
                existing.note = payload.note
            await self.db.flush()
        else:
            entry = RitualEntry(
                ritual_id=ritual_id,
                user_id=user.id,
                entry_date=today,
                status=payload.status,
                note=payload.note,
            )
            self.db.add(entry)
            await self.db.flush()

        await self._recalculate_streaks(ritual)

        partner = await self._get_partner(user)
        partner_entry = await self._get_entry(ritual_id, partner.id, today) if partner else None
        my_entry = await self._get_entry(ritual_id, user.id, today)

        return RitualWithStatusResponse(
            ritual=self._to_response(ritual),
            my_status=my_entry.status if my_entry else None,
            partner_status=partner_entry.status if partner_entry else None,
        )

    async def _get_owned(self, ritual_id: UUID, user: User) -> Ritual:
        if not user.couple_id:
            raise CoupleRequiredError()

        ritual = await self.db.get(Ritual, ritual_id)
        if not ritual:
            raise NotFoundError("Ritual")
        if ritual.couple_id != user.couple_id:
            raise ForbiddenError()
        return ritual

    async def _get_entry(
        self, ritual_id: UUID, user_id: UUID, entry_date: date
    ) -> RitualEntry | None:
        r = await self.db.execute(
            select(RitualEntry).where(
                RitualEntry.ritual_id == ritual_id,
                RitualEntry.user_id == user_id,
                RitualEntry.entry_date == entry_date,
            )
        )
        return r.scalar_one_or_none()

    async def _get_partner(self, user: User) -> User | None:
        if not user.couple_id:
            return None
        r = await self.db.execute(
            select(User).where(
                User.couple_id == user.couple_id,
                User.id != user.id,
            )
        )
        return r.scalar_one_or_none()

    async def _recalculate_streaks(self, ritual: Ritual) -> None:
        distinct_dates = await self.db.execute(
            select(RitualEntry.entry_date)
            .where(
                RitualEntry.ritual_id == ritual.id,
                RitualEntry.status == RitualStatus.COMPLETED    
            )
            .distinct()
            .order_by(RitualEntry.entry_date.desc())
        )
        dates = [row[0] for row in distinct_dates.all()]

        if not dates:
            ritual.current_streak = 0
            await self.db.flush()
            return

        today = date.today()

        if dates[0] not in (today, today - timedelta(days=1)):
            ritual.current_streak = 0
        else:
            streak = 0
            for i, d in enumerate(dates):
                expected = dates[0] - timedelta(days=i)
                if d == expected:
                    streak += 1
                else:
                    break
            ritual.current_streak = streak

        longest = 0
        current_run = 0
        sorted_asc = sorted(set(dates))
        for i, d in enumerate(sorted_asc):
            if i == 0 or d == sorted_asc[i - 1] + timedelta(days=1):
                current_run += 1
                longest = max(longest, current_run)
            else:
                current_run = 1

        ritual.longest_streak = max(ritual.longest_streak, longest)
        await self.db.flush()

    def _to_response(self, ritual: Ritual) -> RitualResponse:
        return RitualResponse(
            id=ritual.id,
            title=ritual.title,
            description=ritual.description or None,
            icon=ritual.icon,
            is_active=ritual.is_active,
            current_streak=ritual.current_streak,
            longest_streak=ritual.longest_streak,
            created_at=ritual.created_at,
        )
