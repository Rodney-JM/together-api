from sqlalchemy import Index, String, Integer, Boolean, UniqueConstraint, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infra.db.base import (
    Base, UUIDMixin, TimestampMixin
)
from domain.enums.plan_tier import PlanTier
from domain.enums.billing_interval import BillingInterval

class Plan(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "plans"
    __table_args__ = (
        UniqueConstraint("tier", "billing_interval", name="uq_plan_tier_interval"),
        Index("ix_plans_tier", "tier")
    )
    
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    tier: Mapped[PlanTier] = mapped_column(Enum(PlanTier), nullable=False)
    billing_interval: Mapped[BillingInterval | None] = mapped_column(
        Enum(BillingInterval), nullable=True
    )
    stripe_price_id: Mapped[str | None] = mapped_column(String(64), nullable=True, unique=True)
    price_cents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="BRL", nullable=False)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    #limits
    max_albums: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_album_photos: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_rituals: Mapped[int | None] = mapped_column(Integer, nullable=True)
    can_use_night_together: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    can_use_watch_together: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    can_send_surprises: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    can_write_letters: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    subscriptions: Mapped[list["Subscription"]] = relationship("Subscription", back_populates="plan")