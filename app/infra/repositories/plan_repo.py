from app.infra.repositories.base import BaseRepository
from app.domain.models.plan import Plan, PlanTier

from sqlalchemy import select

class PlanRepository(BaseRepository[Plan]):
    model = Plan
    
    async def get_free_plan(self) -> Plan | None:
        r = await self.session.execute(select(Plan).where(Plan.tier == PlanTier.FREE, Plan.is_active == True))
        
        return r.scalar_one_or_none
    
    async def get_by_stripe_price_id(self, price_id: str) -> Plan | None:
        r = await self.session.execute(
            select(Plan).where(Plan.stripe_price_id == price_id)
        )
        
        return r.scalar_one_or_none()
    
    async def get_all_active(self) -> list[Plan]:
        r = await self.session.execute(select(Plan).where(Plan.is_active == True))
        return list(r.scalars().all())