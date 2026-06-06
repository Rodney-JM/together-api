from __future__ import annotations

import json
from datetime import datetime, timezone
from nt import error
from uuid import UUID

from pydantic import MongoDsn
import stripe
import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession

from stripe.error import SignatureVerificationError
from app.application.schemas.billing import (
    CheckoutSessionResponse,
    CustomerPortalResponse,
    PlanResponse,
    SubscriptionResponse,
)

from app.core.config import settings
from app.core.exceptions import (
    ActiveSubscriptionError,
    NotFoundError,
    PremiumRequiredError,
    StripeWebhookError
)
from app.core.logging_config import get_logger
from app.domain.enums.billing_interval import BillingInterval
from app.domain.enums.plan_tier import PlanTier
from app.domain.enums.subscription_status import SubscriptionStatus

from app.domain.models.user import User
from app.domain.models.subscription import Subscription
from app.domain.models.plan import Plan
from app.domain.models.couple_models.audit_log import AuditLog
from app.infra.cache.premium_cache import PremiumCache

from app.infra.repositories.plan_repo import PlanRepository
from app.infra.repositories.subscription_repo import SubscriptionRepository
from app.infra.repositories.subscription_event_repo import SubscriptionEventRepository
from app.infra.repositories.user_repo import UserRepository

logger = get_logger(__name__)

def _configure_stripe() -> None:
    if not settings.STRIPE_SECRET_KEY:
        logger.warning("stripe_secret_key_not_configured")
        return
    stripe.api_key = settings.STRIPE_SECRET_KEY

_configure_stripe()

class SubscriptionService:
    def __init__(self, db: AsyncSession, redis: aioredis.Redis) -> None:
        self.db = db
        self.redis = redis
        self.plans = PlanRepository(db)
        self.subscriptions = SubscriptionRepository(db)
        self.subscription_events = SubscriptionEventRepository(db)
        self.users = UserRepository(db)
        self.premium_cache = PremiumCache(redis)
        
    #public api
    async def get_plans(self) -> list[PlanResponse]:
        plans = await self.plans.get_all_active()
        return [PlanResponse.model_validade(p) for p in plans]
    
    async def get_my_subscription(self, user: User) -> SubscriptionResponse | None:
        sub = await self.subscriptions.get_by_user(user.id)
        if not sub:
            return None
        return SubscriptionResponse.model_validate(sub)
    
    async def create_checkout_session(self, user: User, billing_interval: BillingInterval) -> CheckoutSessionResponse:
        existing = await self.subscriptions.get_by_user(user.id)
        if existing and existing.is_premium_active and existing.plan == PlanTier.PREMIUM:
            raise ActiveSubscriptionError()
        
        stripe_customer_id = await self._ensure_stripe_customer(user)
        
        price_id = (
            settings.STRIPE_PRICE_PREMIUM_MONTHLY
            if billing_interval == BillingInterval.MONTHLY
            else settings.STRIPE_PRICE_PREMIUM_YEARLY
        )
        if not price_id:
            raise NotFoundError("Plan not found")
        
        trial_days = settings.STRIPE_TRIAL_DAYS if settings.STRIPE_TRIAL_DAYS > 0 else None
        
        #idempotency key prevents double-charging if request retries
        idempotency_key = f"checkout={user.id}-{billing_interval.value}"
        
        session = stripe.checkout.Session.create(
            customer=stripe_customer_id,
            mode="subscription",
            line_items=[{"price": price_id, "quantity": 1}],
            subscription_data={
                "trial_period_days": trial_days,
                "metadata": {"user_id": str(user.id)}
            },
            metadata={"user_id": str(user.id)},
            success_url=settings.STRIPE_SUCCESS_URL + f"?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=settings.STRIPE_CANCEL_URL,
            allow_promotion_codes=True,
            billing_address_collection="auto",
            idempotency_key=idempotency_key
        )
        
        logger.info("checkout_session_created", user_id=str(user.id), session_id=session.id)
        return CheckoutSessionResponse(checkout_url=session.url, session_id=session.id)
        
    
    async def get_customer_portal(self, user: User) -> CustomerPortalResponse:
        #generates a stripe customer portal url
        stripe_customer_id = user.stripe_customer_id
        if not stripe_customer_id:
            raise NotFoundError("Cliente Stripe")
        
        session = stripe.billing_portal.Session.create(
            customer=stripe_customer_id,
            return_url=settings.STRIPE_CANCEL_URL.replace("/cancel", "/settings")
        )
        
        return CustomerPortalResponse(portal_url=session.url)
    
    #webhook handler
    async def handle_webhook(self, payload: bytes, signature: str) -> None:
        #process a Stripe webhook event
        event = self._verify_webhook_signature(payload, signature)
        
        stripe_event_id = event["id"]
        event_type = event["type"]
        raw_payload = json.dumps(event, default=str)
        
        logger.info("webhook_received", event_id=stripe_event_id, event_type=event_type)
        
        if await self.subscription_events.exists_by_stripe_event_id(stripe_event_id):
            logger.info("webhook_duplicate_skipped",
                        event_id=stripe_event_id)
            return
        
        error: str | None = None
        user_id: UUID | None = None
        stripe_sub_id: str | None = None
        
        try:
            result = await self._disp
    
    #webhook dispatch
    async def _dispatch(self, event: dict) -> dict:
        event_type = event["type"]
        data = event["data"]["object"]
        result: dict = {}
        
        if event_type == "checkout.session.completed":
            result = await self._on_checkout_completed(data)
        
        elif event_type in ("customer.subscription.updated", "customer.subscription.created"):
            result = await self._on_subscription_updated(data)
    
    async def _on_subscription_updated(self, data: dict) -> dict:
        stripe_sub_id = data.get("id")
        user = await self._find
    
    
    async def _on_checkout_completed(self, data: dict) -> dict:
        stripe_customer_id = data.get("customer")
        stripe_sub_id = data.get("subscription")
        user_id_str = data.get("metadata", {}).get("user_id")
        
        if not user_id_str:
            logger.error("checkout_missing_user_id_metadata")
            return {}
        
        user = await self.users.get_by_id(user_id_str)
        if not user:
            logger.error("checkout_user_not_found",user_id= user_id_str),
            return {}
        
        #persist stripe customer id for future portal access
        if stripe_customer_id and not user.stripe_customer_id:
            user.stripe_customer_id = stripe_customer_id
            
        stripe_sub = stripe.Subscription.retrieve(stripe_sub_id)
        await self._upsert_subscription(user, stripe_sub)
        
        logger.info("checkout_completed", user_id=user_id_str, stripe_sub_id=stripe_sub_id)
        return {"user_id": user.id, "stripe_sub_id": stripe_sub_id}
        
    async def _upsert_subscription(self, user: User, stripe_sub: dict) -> None:
        stripe_sub_id = stripe_sub.get("id")
        stripe_price_id = stripe_sub["items"]["data"][0]["price"]["id"]
        
        plan = await self.plans.get_by_stripe_price_id(stripe_price_id)
        if not plan:
            logger.error("plan_not_found_for_price",
                         price_id=stripe_price_id)
            return
        
        status_map = {
            "trialing": SubscriptionStatus.TRIALING,
            "active": SubscriptionStatus.ACTIVE,
            "past_due": SubscriptionStatus.PAST_DUE,
            "canceled": SubscriptionStatus.CANCELED,
            "incomplete": SubscriptionStatus.INCOMPLETE,
            "unpaid": SubscriptionStatus.UNPAID,
        }
        
        status = status_map.get(stripe_sub.get("status", ""),SubscriptionStatus.INCOMPLETE)
        
        sub = await self.subscriptions.get_by_user(user.id)
        if sub:
            sub.plan_id = plan.id
            sub.stripe_subscription_id = stripe_sub_id
            sub.stripe_customer_id = stripe_sub.get("customer")
            sub.status = status
            sub.cancel_at_period_end = stripe_sub.get("cancel_at_period_end", False)
            sub.canceled_at = (
                datetime.fromtimestamp(stripe_sub["canceled_at"], tz=timezone.utc)
                if stripe_sub.get("canceled_at")
                else None
            )
        else:
            sub = Subscription(
                user_id=user.id,
                plan_id=plan.id,
                stripe_subscription_id=stripe_sub_id,
                stripe_customer_id=stripe_sub.get("customer"),
                status=status,
                cancel_at_period_end=stripe_sub.get("cancel_at_period_end", False)
            )
            self.db.add(sub)
        
        #update billing period
        period = stripe_sub.get("current_period_start"), stripe_sub.get("current_period_end")
        if period[0]:
            sub.current_period_start = datetime.fromtimestamp(period[0], tz=timezone.utc)
        if period[1]:
            sub.current_period_end = datetime.fromtimestamp(period[1], tz=timezone.utc)
        
        trial_end = stripe_sub.get("trial_end")
        if trial_end:
            sub.trial_end = datetime.fromtimestamp(trial_end, tz=timezone.utc)
        
        await self.db.flush()
        
        #invalidate cache
        is_premium = status in (
            SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING, SubscriptionStatus.PAST_DUE
        ) and plan.tier == PlanTier.PREMIUM
        await self.premium_cache.set(str(user.id), is_premium)
        
        logger.info(
            "subscription_upserted",
            user_id=str(user.id),
            plan=plan.name,
            status=status.value
        )
    
    async def _find_user_by_stripe_customer(self, stripe_customer_id: str | None) -> User | None:
        if not stripe_customer_id:
            return None
        return await self.users.get_by_stripe_customer_id(stripe_customer_id)
    
    
    def _verify_webhook_signature(self, payload: bytes, signature: str) -> dict:
        #primary defence against fake/forged webhook attacks
        if not settings.STRIPE_WEBHOOK_SECRET:
            if settings.is_production:
                raise StripeWebhookError("Webhook secret não configurado")
            logger.warning("webhook_secret_not_configured_dev_mode")
            try:
                return json.loads(payload)
            except Exception:
                raise StripeWebhookError("Payload inválido")
            
        try:
            return stripe.Webhook.construct_event(payload, signature, settings.STRIPE_WEBHOOK_SECRET)
        except SignatureVerificationError as exc:
            logger.warning("webhook_signature_invalid", error=str(exc))
            raise StripeWebhookError("Assinatura do webhook inválida") from exc
        except Exception as exc:
            raise StripeWebhookError(f"Erro ao processar webhook: {exc}") from exc
    
    async def _ensure_stripe_customer(self, user: User) -> str:
        """
        get or create a stripe customer for this user
        """
        
        if user.stripe_customer_id:
            return user.stripe_customer_id
        
        customer = stripe.Customer.create(
            email=user.email,
            name=user.name,
            metadata={"user_id": str(user.id)}
        )
        
        user.stripe_customer_id = customer.id
        await self.db.flush()
        return customer.id