from sqlalchemy import Index, String, ForeignKey, DateTime, Boolean, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.infra.db.base import (
    Base,
    UUIDMixin,
    TimestampMixin
)
from app.domain.enums.subscription_status import SubscriptionStatus
from app.domain.enums.plan_tier import PlanTier
from datetime import datetime
import uuid


class Subscription(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "subscriptions"
    __table_args__ = (
        Index("ix_subscriptions_user_id", "user_id"),
        Index("ix_subscriptions_stripe_subscription_id", "stripe_subscription_id", unique=True),
        Index("ix_subscriptions_status", "status")
    )
    
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("plans.id", ondelete="RESTRICT"), nullable=False
    )
    
    stripe_subscription_id: Mapped[str | None] = mapped_column(String(64), nullable=True, unique=True)
    stripe_customer_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    
    status: Mapped[SubscriptionStatus] = mapped_column(
        Enum(SubscriptionStatus), default=SubscriptionStatus.ACTIVE, nullable=False
    )
    
    current_period_start: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    current_period_end: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    trial_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    canceled_at: Mapped[datetime | None] = mapped_column(timezone=True, nullable=True)
    
    cancel_at_period_end: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    user: Mapped["User"] = relationship("User", back_populates="subscription")
    plan: Mapped["Plan"] = relationship("Plan", back_populates="subscriptions", lazy="selectin")
    
    @property
    def is_premium_active(self) -> bool:
        return self.status in (
            SubscriptionStatus.ACTIVE,
            SubscriptionStatus.TRIALING,
            SubscriptionStatus.PAST_DUE
        ) and self.plan.tier == PlanTier.PREMIUM