import uuid 
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infra.db.base import (
    Base, 
    TimestampMixin,
    UUIDMixin
)

class SpecialDate(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "special_dates"
    __table_args__ = (Index("ix_special_dates_couple_id", "couple_id"),)
    
    couple_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("couples.id", ondelete="CASCADE"),
        nullable=False
    )
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    title: Mapped[str] = mapped_column(
        String(150), nullable=False
    )
    icon: Mapped[str] = mapped_column(
        String(10), default="📅", nullable=False
    )
    event_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    is_recurring_yearly: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notify_days_before: Mapped[int] = mapped_column(Integer, default=7, nullable=False)
    notes: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )