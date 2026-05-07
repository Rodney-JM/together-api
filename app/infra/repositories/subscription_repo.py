from app.infra.repositories.base import BaseRepository
from app.domain.models.subscription import Subscription, SubscriptionStatus

from uuid import UUID
from datetime import datetime
from sqlalchemy import select

class SubscriptionRepository(BaseRepository[Subscription]):
    model = Subscription
    
    async def get_by_user(self, user_id: UUID) -> Subscription | None:
        r = await self.session.execute(
            select(Subscription).where(Subscription.user_id == user_id)
        )
        
        return r.scalar_one_or_none()
    
    async def get_by_stripe_subscription_id(self, stripe_sub_id: str) -> Subscription | None:
        r = await self.session.execute(
            select(Subscription).where(Subscription.stripe_subscription_id == stripe_sub_id)
        )
        
        return r.scalar_one_or_none
    
    async def get_expiring_soon(self, cutoff: datetime) -> list[Subscription]:
        r = await self.session.execute(
            select(Subscription).where(
                Subscription.status.in_([SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING]),
                Subscription.current_period_end <= cutoff
            )
        )
        return list(r.scalars().all())