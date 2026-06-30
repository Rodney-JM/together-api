from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.schemas.album import AlbumResponse, AlbumUpdate, AlbumCreate
from app.application.schemas.memory import MemoryResponse
from app.application.schemas.common import PaginatedResponse
from app.core.exceptions import ForbiddenError, NotFoundError, SubscriptionLimitError

from app.domain.models.album import Album
from app.domain.models.memory import Memory
from app.domain.models.user import User

from app.infra.repositories.album_repo import AlbumRepository
from app.infra.repositories.memory_repo import MemoryRepository
from app.infra.storage.storage_service import get_presigned_url
from app.application.services.domain_services.helpers import _get_plan


class AlbumService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.album_repo = AlbumRepository(db)
        self.memory_repo = MemoryRepository(db)

    async def create_album(self, user: User, payload: AlbumCreate) -> AlbumResponse:
        plan = await _get_plan(user, self.db)
        if plan and plan.max_albums is not None:
            count = await self.album_repo.count(Album.couple_id == user.couple_id)
            if count >= plan.max_albums:
                raise SubscriptionLimitError(
                    f"Limite de {plan.max_albums} álbuns atingido no plano. "
                    "Faça o upgrade para o Premium para criar álbuns ilimitados"
                )

        album = Album(
            couple_id=user.couple_id,
            title=payload.title,
            description=payload.description,
        )
        album = await self.album_repo.add(album)
        return self._to_response(album)

    async def list_photos(
        self, user: User, album_id: UUID, *, category: str | None = None, page: int = 1, page_size: int = 30
    ) -> PaginatedResponse[MemoryResponse]:
        album = await self._get_owned(album_id, user)
        
        filters = [
            Memory.couple_id == user.couple_id,
            Memory.album_id == album_id,
        ]
        if category:
            filters.append(Memory.category == category)

        offset = (page - 1) * page_size
        items = await self.memory_repo.get_all(
            filters=filters,
            order_by=Memory.created_at.desc(),
            limit=page_size,
            offset=offset,
        )
        total = await self.memory_repo.count(*filters)

        return PaginatedResponse(
            items=[self._to_memory_response(m) for m in items],
            total=total,
            page=page,
            page_size=page_size,
            has_next=(offset + len(items)) < total,
        )

    async def get_recent(self, user: User, limit: int = 5) -> list[AlbumResponse]:
        items = await self.album_repo.get_all(
            filters=[Album.couple_id == user.couple_id],
            order_by=Album.created_at.desc(),
            limit=limit,
        )
        return [self._to_response(a) for a in items]

    async def update_album(self, user: User, album_id: UUID, payload: AlbumUpdate) -> AlbumResponse:
        album = await self._get_owned(album_id, user)
        update_data = payload.model_dump(exclude_unset=True)
        album = await self.album_repo.update(album, update_data)
        return self._to_response(album)

    async def delete_album(self, user: User, album_id: UUID) -> None:
        album = await self._get_owned(album_id, user)
        memories = await self.memory_repo.get_memories_by_album_id(album_id)
        if memories:
            raise ForbiddenError("Não é permitido excluir álbuns que contenham memórias.")
        await self.album_repo.delete(album)

    async def _get_owned(self, album_id: UUID, user: User) -> Album:
        album = await self.album_repo.get_by_id(album_id)
        if not album:
            raise NotFoundError("Album")
        if album.couple_id != user.couple_id:
            raise ForbiddenError()
        return album

    def _to_response(self, album: Album) -> AlbumResponse:
        return AlbumResponse(
            id=str(album.id),
            couple_id=str(album.couple_id),
            title=album.title,
            description=album.description,
            cover_memory_id=album.cover_memory_id,
            created_at=album.created_at,
            updated_at=album.updated_at,
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
            updated_at=memory.updated_at,
        )
