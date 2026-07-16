from datetime import datetime

from app.domain.enums.relationship_status import RelationshipStatus
from app.domain.enums.subscription_status import SubscriptionStatus
from sqlalchemy import ForeignKey, func, String, DateTime, Boolean, Enum, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infra.db.base import (
    Base,
    UUIDMixin,
    TimestampMixin     
)
import uuid

class Couple(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "couples"
    __table_args__ = (Index("ix_couples_invite_code", "invite_code", unique=True),)
    
    invite_code: Mapped[str] = mapped_column(
        String(12), unique=True, nullable=False, index=True
    )
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    relationship_start_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    relationship_status: Mapped[RelationshipStatus] = mapped_column(
        Enum(RelationshipStatus),
        default=RelationshipStatus.dating
    )
    
    current_streak: Mapped[int] = mapped_column(default=0, nullable=False)
    longest_streak: Mapped[int] = mapped_column(default=0, nullable=False)
    last_activity_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    
    cover_image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    """ invite_code: Mapped[str] = mapped_column(
        String(20),
        unique=True, 
        default=lambda: str(uuid.uuid4())[:8]
    ) """
    
    
    subscription_status: Mapped[SubscriptionStatus] = mapped_column(
        Enum(SubscriptionStatus),
        default=SubscriptionStatus.ACTIVE
    )
    subscription_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    members: Mapped[list["User"]] = relationship(
        "User",
        foreign_keys="User.couple_id",
        back_populates="couple",
        lazy="selectin"
    )
    
    def __repr__(self) -> str:
        return f"<Couple {self.id}>"
    
    @property
    def partner_ids(self) -> list[str]:
        return [m.user_id for m in self.members]