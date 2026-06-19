from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select, func
from fastapi import UploadFile

from app.application.schemas.album import AlbumResponse
from app.core.exceptions import ForbiddenError, NotFoundError, SubscriptionLimitError

from app.domain.models import Album
from app.domain.models.memory import Memory
from app.domain.models.user import User

from app.application.schemas.memory import MemoryUploadRequest
from app.application.schemas.memory import MemoryResponse
from app.application.schemas.album import AlbumUpdate, AlbumResponse, AlbumCreate
from app.application.schemas.common import PaginatedResponse

from app.infra.storage.storage_service import upload_file
from app.infra.storage.storage_service import delete_file
from app.infra.storage.storage_service import get_presigned_url
from app.application.services.domain_services.helpers import _get_plan

class AlbumService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        
    async def create_album(self, user: User, payload: AlbumCreate) -> AlbumResponse:
        plan = await _get_plan(user, self.db)
        if plan and plan.max_albums is not None:
            r = await self.db.execute(
                select(func.count()).select_from(Album)
                .where(Album.couple_id == user.couple_id)
            )
            count = r.scalar_one()
            if count>= plan.max_albums:
                raise SubscriptionLimitError(f"Limite de {plan.max_albums} álbuns atingido no plano." "Faça o upgrade para o Premium para criar álbuns ilimitados")
        
        new_album = Album(
            couple_id=user.couple_id,
            title=payload.title,
            description=payload.description,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        self.db.add(new_album)
        await self.db.flush()
        
        return self._to_response(new_album)
    
    async def list_photos(
        self, user: User, album_id: UUID, *, category: str | None = None, page: int = 1, page_size: int = 30
    ) -> PaginatedResponse[MemoryResponse]:
        filters = [
            Memory.couple_id == user.couple_id,
            Memory.album_id == album_id
        ]
        
        if category:
            filters.append(Memory.category == category)

        offset = (page - 1) * page_size
        r = await self.db.execute(
            select(Memory).where(*filters)
            .order_by(Memory.created_at.desc())
            .limit(page_size).offset(offset)
        )
        items = r.scalars().all()

        total_r = await self.db.execute(
            select(func.count()).select_from(Memory).where(*filters)
        )
        total = total_r.scalar_one()
        return PaginatedResponse(
            items=[self._to_memory_response(p) for p in items],
            total=total, page=page, page_size=page_size,
            has_next=(offset + len(items)) < total,
        )
    
    async def get_recent(self, user: User, limit: int = 5) -> list[AlbumResponse]:
        r = await self.db.execute(
            select(Album).where(Album.couple_id == user.couple_id)
            .order_by(Album.created_at.desc()).limit(limit)
        )
        
        return [self._to_album_response(p) for p in r.scalars().all()]
    
    async def update_album(self, user: User, album_id: UUID, payload: AlbumUpdate) -> AlbumResponse:
        album = await self._get_owned(album_id, user)
        if payload.title is not None:
            album.title = payload.title
        if payload.description is not None:
            album.description = payload.description

        album.updated_at = datetime.now(timezone.utc)

        await self.db.flush()
        return self._to_album_response(album)
    
    async def delete_album(self, user: User, album_id: UUID) -> None:
        album = await self._get_owned(album_id, user)
        r = await self.db.execute(
            select(Memory).where(
                Memory.album_id == album_id,
                Memory.couple_id == user.couple_id
            )
        )
        memories = r.scalars().all()
        if memories:
            raise ForbiddenError("Não é permitido excluir álbuns que contenham memórias.")

        await self.db.delete(album)
        await self.db.flush()
        
    async def _get_owned(self, album_id: UUID, user: User) -> Album:
        album = await self.db.get(Album, album_id)
        if not album:
            raise NotFoundError("Album")
        if album.couple_id != user.couple_id:
            raise ForbiddenError()
        return album
    
    def _to_album_response(self, album: Album) -> AlbumResponse:
        return AlbumResponse(
            id=str(album.id),
            couple_id=str(album.couple_id),
            title=album.title,
            description=album.description,
            cover_memory_id=album.cover_memory_id if album.cover_memory_id else None,
            created_at=album.created_at,
            updated_at=album.updated_at,
            memories=[
                memory for memory in getattr(album, "memories", [])
            ] if hasattr(album, "memories") and album.memories else []
        )
        
    def _to_memory_response(self, memory: Memory) -> MemoryResponse:
        url = get_presigned_url(memory.s3_key)
        return MemoryResponse(
            id=str(memory.id),
            album_id=str(memory.album_id),
            author_id=str(memory.author_id),
            title=memory.caption or "",
            note=memory.caption,
            media_url=url,
            created_at=memory.created_at,
            updated_at=memory.updated_at
        )