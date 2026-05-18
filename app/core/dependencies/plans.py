from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.user import User
from app.domain.models.plan import Plan
from app.domain.models.ritual import Ritual
from app.domain.models.memory import Memory

from app.core.exceptions import SubscriptionLimitError
from app.infra.repositories.subscription_repo import SubscriptionRepository

async def get_user_plan(user: User, db: AsyncSession) -> Plan | None:
    sub_repo = SubscriptionRepository(db)
    sub = await sub_repo.get_by_user(user.id)
    return sub.plan if sub else None

async def assert_album_limit(user: User, db: AsyncSession) -> None:
    plan = await get_user_plan(user, db)
    if plan is None or plan.max_album_photos is None:
        return
    
    memories = await db.execute(
        select(func.count()).select_from(Memory).where(
            Memory.couple_id == user.couple_id
        )
    )
    
    count = memories.scalar_one()
    if count >= plan.max_album_photos:
        raise SubscriptionLimitError(
            f"Você atingiu o limite de {plan.max_album_photos} fotos do plano."
            "Faça um upgrade e tenha fotos ilimitadas."
        )

async def assert_ritual_limit(user: User, db: AsyncSession) -> None:
    plan = await get_user_plan(user, db)
    if plan is None or plan.max_rituals is None:
        return
    
    rituals = await db.execute(
        select(func.count()).select_from(Ritual).where(
            Ritual.couple_id == user.couple_id, Ritual.is_active == True
        )
    )
    count = rituals.scalar_one()
    if count >= plan.max_rituals:
        raise SubscriptionLimitError(
            f"Plano gratuito permite até {plan.max_rituals} rituais ativos. "
            "Faça upgrade para criar rituais ilimitados."
        )