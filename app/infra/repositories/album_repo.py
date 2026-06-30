from uuid import UUID

from app.domain.models.album import Album
from app.infra.repositories.base import BaseRepository

class AlbumRepository(BaseRepository[Album]):
    model = Album
    
    async def get_by_couple_paginated(
        self,
        couple_id: UUID,
        *,
        limit: int = 30,
        offset: int = 0
    ) -> tuple[list[Album], int]:
        filters = [Album.couple_id==couple_id]
        
        items = await self.get_all(
            filters=filters,
            order_by=Album.created_at.desc(),
            limit=limit,
            offset=offset
        )
        total = await self.count(*filters)
        return items, total