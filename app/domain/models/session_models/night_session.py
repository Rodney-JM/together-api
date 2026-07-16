import uuid

from datetime import datetime
from app.infra.db.base import (
    Base, UUIDMixin, TimestampMixin
)
from sqlalchemy import Index, String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.domain.enums.night_session_status import NightSessionStatus

class NightSession(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "night_sessions"
    __table_args__ = (Index("ix_night_sessions_couple_id", "couple_id"),)
    
    couple_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("couples.id", ondelete="CASCADE"),
        nullable=False    
    )
    
    status: Mapped[NightSessionStatus] = mapped_column(
        String(20),
        default=NightSessionStatus.WAITING, nullable=False
    )
    ambient_sound: Mapped[str] = mapped_column(
        String(50),
        default="silence", nullable=False
    )
    
    user1_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    
    user1_joined_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    user2_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    user2_joined_at: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    user1: Mapped["User"] = relationship("User", foreign_keys=[user1_id])
    user2: Mapped["User"] = relationship("User", foreign_keys=[user2_id])
    