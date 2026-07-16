import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, ForeignKey, Index, Integer, String, Text, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.enums.ritual_status import RitualStatus
from app.infra.db.base import (
    Base,
    UUIDMixin,
    TimestampMixin
)

class Ritual(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "rituals"
    __table_args__ = (Index("ix_rituals_couple_id", "couple_id"),)
    
    couple_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("couples.id", ondelete="CASCADE"),
        nullable=False
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("couples.id", ondelete="CASCADE"),
        nullable=False
    )
    
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(300), nullable=False)
    icon: Mapped[str] = mapped_column(String(10), default="✨", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    current_streak: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    longest_streak: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    entries: Mapped[list["RitualEntry"]] = relationship(
        "RitualEntry",
        back_populates="ritual",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
    
    def __repr__(self) -> str:
        return f"<Ritual '{self.title}'>"
    
class RitualEntry(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "ritual_entries"
    __table_args__ = (
        Index("ix_ritual_entries_ritual_date", "ritual_id", "entry_date"),
        Index("ix_ritual_entries_user_date", "user_id", "entry_date")
    )
    
    ritual_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("rituals.id", ondelete="CASCADE"),
        nullable=False
    )
    
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    
    entry_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[RitualStatus] = mapped_column(
        Enum(RitualStatus), default=RitualStatus.COMPLETED, nullable=False
    )
    note: Mapped[str | None] = mapped_column(String(300), nullable=True)
    ritual: Mapped[Ritual] = relationship("Ritual", back_populates="entries")
    user: Mapped["User"] = relationship("User")