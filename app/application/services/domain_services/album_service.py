from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import UploadFile

from app.application.schemas.album

class AlbumService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        
    async def upload_photo(
        self, user: User, file: UploadFile, meta: PhotoUploadRequest
    ) -> AlbumPhotoResponse:
        from app.infrastructure.storage.s3_client import upload_file

        # Enforce quantitative limit for Free tier
        plan = await _get_plan(user, self.db)
        if plan and plan.max_album_photos is not None:
            r = await self.db.execute(
                select(func.count()).select_from(AlbumPhoto)
                .where(AlbumPhoto.couple_id == user.couple_id)
            )
            count = r.scalar_one()
            if count >= plan.max_album_photos:
                raise SubscriptionLimitError(
                    f"Limite de {plan.max_album_photos} fotos atingido no plano gratuito. "
                    "Faça upgrade para o Premium."
                )

        s3_key, size = await upload_file(file, str(user.couple_id), "album")
        photo = AlbumPhoto(
            couple_id=user.couple_id, uploaded_by=user.id,
            s3_key=s3_key, original_filename=file.filename or "upload",
            caption=meta.caption, category=meta.category.value,
            file_size_bytes=size,
        )
        self.db.add(photo)
        await self.db.flush()
        return self._to_response(photo)