import uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime, Numeric, Boolean, Index, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from datetime import datetime
from app.infra.db.base import (
    Base,
    UUIDMixin,
    TimestampMixin
)

class WatchSession(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "watch_sessions"
    __table_args__ = (Index("ix_watch_sessions_couple_id", "couple_id"),)
    
    couple_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("couples.id", ondelete="CASCADE"),
        nullable=False
    )
    initiated_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    
    media_title: Mapped[str] = mapped_column(String(200), nullable=False)
    media_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    media_type: Mapped[str] = mapped_column(String(30), default="external", nullable=False)
    
    #playback state
    is_playing: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    current_position_seconds: Mapped[float] = mapped_column(
        Numeric(12, 3), default=0.0,
        nullable=False
    )
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )