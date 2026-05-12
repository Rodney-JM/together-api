from app.domain.models.memory import Memory
from app.infra.repositories.base import BaseRepository
from uuid import UUID

from sqlalchemy import select 

class MemoryRepository(BaseRepository[Memory]):
    model = Memory
    
    async def get_memories_by_couple_id(self, couple_id: UUID) -> list[Memory]:
        r = await self.session.execute(
            select(Memory).where(Memory.couple_id == couple_id)
        )
        
        return list(r.scalars().all())
    
    
    async def get_memories_by_album_id(self, album_id: UUID) -> list[Memory]:
        r = await self.session.execute(
            select(Memory).where(Memory.album_id == album_id)
        )
        
        return list(r.scalars().all())