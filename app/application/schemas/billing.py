from __future__ import annotations

from datetime import datetime 
from uuid import UUID

from pydantic import BaseModel

from app.domain.enums.billing_interval import BillingInterval
from app.domain.enums.plan_tier import PlanTier
from app.domain.enums.subscription_status import SubscriptionStatus

class PlanResponse(BaseModel):
    id: UUID
    name: str
    tier: PlanTier
    billing_interval: BillingInterval | None
    price_cents: int
    currency: str
    
    max_album_photos: int | None
    max_rituals: int | None
    can_use_night_together: bool
    can_use_watch_together: bool
    can_send_surprises: bool
    can_write_letters: bool
    
    model_config = {"from_attributes": True}
    

class SubscriptionResponse(BaseModel):
    id: UUID
    plan: PlanResponse
    status: SubscriptionStatus
    current_period_start: datetime | None
    current_period_end: datetime | None
    trial_end: datetime | None
    cancel_at_period_end: bool
    canceled_at: datetime | None
    is_premium_active: bool
    
    model_config = {"from_attributes": True}
    
class CheckoutSessionRequest(BaseModel):
    billing_interval: BillingInterval

class CheckoutSessionResponse(BaseModel):
    checkout_url: str
    session_id: str

class CustomerPortalResponse(BaseModel):
    portal_url: str

class PublicKeyResponse(BaseModel):
    publishable_key: str