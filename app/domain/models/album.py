from sqlalchemy import String, ForeignKey, func, DateTime, BigInteger, Text, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.enums.memory_category import MemoryCategory as AlbumCategory
from app.infra.db.base import(
    Base,
    TimestampMixin,
    UUIDMixin
)

import uuid

class Album(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "albums"
    
    __table_args__ = (
        Index("ix_albums_couple_id", "couple_id"),
        Index("ix_albums_created_by", "created_by"),
        Index("ix_albums_cover_memory_id", "cover_memory_id")
    )
    
    couple_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("couples.id", ondelete="CASCADE"),
        nullable=False
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    title: Mapped[str] = mapped_column(
        String(150), 
        nullable=False
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )
    cover_memory_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("memories.id", ondelete="SET NULL"),
        nullable=True
    )
    
    cover_memory: Mapped["Memory"] = relationship("Memory", foreign_keys=[cover_memory_id])
    memories: Mapped[list["Memory"]] = relationship("Memory", back_populates="album", cascade="all, delete-orphan")
    
    creator: Mapped["User"] = relationship("User", foreign_keys=[created_by], back_populates="albums_created")