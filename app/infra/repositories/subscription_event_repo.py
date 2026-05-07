from app.domain.models.subscription_event import SubscriptionEvent
from app.infra.repositories.base import BaseRepository
from sqlalchemy import select
from uuid import UUID

class SubscriptionEventRepository(BaseRepository[SubscriptionEvent]):
    model = SubscriptionEvent
    
    async def exists_by_stripe_event_id(self, stripe_event_id: str) -> bool:
        r = await self.session.execute(
            select(SubscriptionEvent).where(
                SubscriptionEvent.stripe_event_id == stripe_event_id
            )
        )
        
        return r.scalar_one_or_none() is not None
    
    async def record(
        self,
        *,
        stripe_event_id: str,
        event_type: str,
        payload: str,
        user_id: UUID | None = None,
        stripe_subscription_id: str | None = None,
        error: str | None = None
    ) -> SubscriptionEvent:
        event = SubscriptionEvent(
            stripe_event_id=stripe_event_id,
            event_type=event_type,
            payload=payload,
            user_id=user_id,
            stripe_subscription_id=stripe_subscription_id,
            processed=error is None,
            error=error
        )
        
        self.session.add(event)
        await self.session.flush()
        return event