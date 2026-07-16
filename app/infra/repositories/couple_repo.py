from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.domain.models.couple_models.couple import Couple
from app.infra.repositories.base import BaseRepository

class CoupleRepository(BaseRepository[Couple]):
    model = Couple
    
    async def get_by_id(self, couple_id: UUID) -> Couple:
        query = (
            select(Couple)
            .options(joinedload(Couple.members))
            .where(Couple.id==couple_id)
        )
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_invite_code(self, code: str) -> Couple | None:
        result = await self.session.execute(
            select(Couple).where(Couple.invite_code == code.upper(), Couple.is_active == True)
        )
        return result.scalar_one_or_none()