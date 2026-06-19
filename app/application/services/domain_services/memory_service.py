from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, delete
from fastapi import UploadFile

from app.application.schemas.memory import MemoryResponse, MemoryUploadRequest, MemoryUpdate
from app.application.schemas.common import PaginatedResponse
from app.core.exceptions import ForbiddenError, NotFoundError, SubscriptionLimitError

from app.domain.models.memory import Memory
from app.domain.models.album import Album
from app.domain.models.user import User

from app.infra.storage.storage_service import upload_file, delete_file, get_presigned_url
from app.application.services.domain_services.helpers import _get_plan

class MemoryService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_memory(
        self,
        user: User,
        payload: MemoryUploadRequest,
        file: UploadFile,
    ) -> MemoryResponse:
        album = await self.db.get(Album, payload.album_id)
        if not album:
            raise NotFoundError("Album")
        if album.couple_id != user.couple_id:
            raise ForbiddenError()
        
        plan = await _get_plan(user, self.db)
        if plan and plan.max_album_photos is not None:
            r = await self.db.execute(
                select(func.count()).select_from(Memory)
                .where(
                    Memory.album_id == payload.album_id,
                    Memory.couple_id == user.couple_id
                )
            )
            count = r.scalar_one()
            if count >= plan.max_album_photos:
                raise SubscriptionLimitError(
                    f"Limite de {plan.max_memories_per_album} memórias por álbum atingido no plano. Faça o upgrade para o Premium para criar memórias ilimitadas."
                )
        
        # Upload file, get S3 key
        s3_key = await upload_file(file,user.couple_id , "memory")

        now = datetime.now(timezone.utc)
        new_memory = Memory(
            album_id=payload.album_id,
            couple_id=user.couple_id,
            author_id=user.id,
            s3_key=s3_key,
            caption=payload.caption,
            category=payload.category,
            created_at=now,
            updated_at=now,
        )
        self.db.add(new_memory)
        await self.db.flush()

        # Optionally update album's updated_at
        await self.db.execute(
            update(Album)
            .where(Album.id == payload.album_id)
            .values(updated_at=now)
        )
        await self.db.flush()

        return self._to_memory_response(new_memory)

    async def get_memory(self, user: User, memory_id: UUID) -> MemoryResponse:
        memory = await self.db.get(Memory, memory_id)
        if not memory:
            raise NotFoundError("Memory")
        if memory.couple_id != user.couple_id:
            raise ForbiddenError()
        return self._to_memory_response(memory)

    async def list_memories(
        self,
        user: User,
        album_id: UUID | None = None,
        *,
        category: str | None = None,
        page: int = 1,
        page_size: int = 30
    ) -> PaginatedResponse[MemoryResponse]:
        filters = [Memory.couple_id == user.couple_id]
        if album_id:
            filters.append(Memory.album_id == album_id)
        if category:
            filters.append(Memory.category == category)

        offset = (page - 1) * page_size
        r = await self.db.execute(
            select(Memory)
            .where(*filters)
            .order_by(Memory.created_at.desc())
            .limit(page_size)
            .offset(offset)
        )
        items = r.scalars().all()

        total_r = await self.db.execute(
            select(func.count()).select_from(Memory).where(*filters)
        )
        total = total_r.scalar_one()

        return PaginatedResponse(
            items=[self._to_memory_response(m) for m in items],
            total=total,
            page=page,
            page_size=page_size,
            has_next=(offset + len(items)) < total,
        )

    async def update_memory(
        self,
        user: User,
        memory_id: UUID,
        payload: MemoryUpdate,
    ) -> MemoryResponse:
        memory = await self.db.get(Memory, memory_id)
        if not memory:
            raise NotFoundError("Memory")
        if memory.couple_id != user.couple_id:
            raise ForbiddenError()

        # Only allowed fields
        has_update = False
        if payload.caption is not None:
            memory.caption = payload.caption
            has_update = True
        if payload.category is not None:
            memory.category = payload.category
            has_update = True

        if has_update:
            memory.updated_at = datetime.now(timezone.utc)
            await self.db.flush()

        return self._to_memory_response(memory)

    async def delete_memory(self, user: User, memory_id: UUID) -> None:
        memory = await self.db.get(Memory, memory_id)
        if not memory:
            raise NotFoundError("Memory")
        if memory.couple_id != user.couple_id:
            raise ForbiddenError()

        # Remove S3 object first
        if memory.s3_key:
            await delete_file(memory.s3_key)

        await self.db.delete(memory)
        await self.db.flush()

    def _to_memory_response(self, memory: Memory) -> MemoryResponse:
        url = get_presigned_url(memory.s3_key) if memory.s3_key else None
        return MemoryResponse(
            id=str(memory.id),
            album_id=str(memory.album_id),
            author_id=str(memory.author_id),
            title=memory.caption or "",
            note=memory.caption,
            media_url=url,
            created_at=memory.created_at,
            updated_at=memory.updated_at,
            category=memory.category,
        )