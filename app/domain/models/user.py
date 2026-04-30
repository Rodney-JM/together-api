from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.infra.db.base import (
    Base,
    TimestampMixin,
    UUIDMixin
)
from datetime import datetime

from app.domain.enums.mood_type import MoodType

import uuid

class User(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "users"
    __table_args__ = (
        Index("ix_users_email", "email", unique=True),
        Index("ix_users_couple_id", "couple_id")
    )
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    current_mood: Mapped[MoodType | None] = mapped_column(
        String(30), nullable=True
    )
    mood_updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    couple_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("couples.id", ondelete="SET NULL"),
        nullable=True
    )
    
    stripe_customer_id: Mapped[str | None] = mapped_column(
        String(64), nullable=True, unique=True
    )
    
    couples: Mapped["Couple"] = relationship(
        "Couple",
        foreign_keys=[couple_id],
        back_populates="members"
    )
    
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        "RefreshToken",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    albums: Mapped[list["Album"]] = relationship(
        "Album",
        back_populates="user"
    )
    
    memories: Mapped[list["Memory"]] = relationship("Memory", back_populates="author")
    albums_created: Mapped[list["Album"]] = relationship("Album", back_populates="creator")
    subscription: Mapped["Subscription | None"] = relationship("Subscription", back_populates="user", uselist=False, lazy="selectin")
    
    def __repr__(self) -> str:
        return f"<User {self.email}>"