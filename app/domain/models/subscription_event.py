import uuid
from datetime import datetime

from sqlalchemy import Index, String, DateTime, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from sqlalchemy import func as _func2
from app.infra.db.base import Base, UUIDMixin

class SubscriptionEvent(Base, UUIDMixin):
    __tablename__ = "subscription_events"
    __table_args__ = (
        Index("ix_sub_events_stripe_event_id", "stripe_event_id", unique=True),
        Index("ix_sub_events_user_id", "user_id"),
        Index("ix_sub_events_created_at", "created_at")
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=_func2.now(), nullable=False
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    stripe_event_id: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    event_type: Mapped[str] = mapped_column(String(80), nullable=False)
    stripe_subscription_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    
    payload: Mapped[str] = mapped_column(Text, nullable=False)
    processed: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)