from uuid import UUID

from app.core.config import settings

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.domain.enums.billing_interval import BillingInterval
from app.domain.models.plan import Plan
from app.infra.repositories.plan_repo import PlanRepository
from app.application.schemas.billing import PlanTier
from app.domain.models.subscription import Subscription
from app.domain.enums.subscription_status import SubscriptionStatus

from app.core.logging_config import get_logger

logger = get_logger(__name__)

async def seed_plans(db: AsyncSession) -> None:
    existing = await db.execute(select(Plan))
    
    if existing.scalars().first() is not None:
        return
    
    plans = [
        Plan(
            name="Gratuito",
            tier=PlanTier.FREE,
            billing_interval=None,
            stripe_price_id=None,
            price_cents=0,
            currency="BRL",
            max_album_photos=30,
            max_rituals=3,
            can_use_night_together=False,
            can_use_watch_together=False,
            can_send_surprises=False,
            can_write_letters=True
        ),
        Plan(
            name="Premium Mensal",
            tier=PlanTier.PREMIUM,
            billing_interval=BillingInterval.MONTHLY,
            stripe_price_id=settings.STRIPE_PRICE_PREMIUM_MONTHLY or None,
            price_cents=2990,
            currency="BRL",
            max_album_photos=None,    # unlimited
            max_rituals=None,         # unlimited
            can_use_night_together=True,
            can_use_watch_together=True,
            can_send_surprises=True,
            can_write_letters=True,
        ),
        Plan(
            name="Premium Anual",
            tier=PlanTier.PREMIUM,
            billing_interval=BillingInterval.YEARLY,
            stripe_price_id=settings.STRIPE_PRICE_PREMIUM_YEARLY or None,
            price_cents=24990,  # R$249.90/year — ~30% discount vs monthly
            currency="BRL",
            max_album_photos=None,
            max_rituals=None,
            can_use_night_together=True,
            can_use_watch_together=True,
            can_send_surprises=True,
            can_write_letters=True,
        )
    ]
    
    db.add_all(plans)
    await db.commit()
    logger.info("plans_seeded", count=len(plans))


async def assign_free_plan(user_id: UUID, db: AsyncSession) -> None:
    plan_repo = PlanRepository(db)
    free_plan = plan_repo.get_free_plan()
    if not free_plan:
        logger.error("free_plan_missing_cannot_assign")
        return
    
    sub = Subscription(
        user_id=user_id,
        plan_id=free_plan.id,
        status=SubscriptionStatus.ACTIVE
    )
    db.add(sub)
    await db.flush()
    logger.info("free_plan_assigned", user_id=str(user_id))