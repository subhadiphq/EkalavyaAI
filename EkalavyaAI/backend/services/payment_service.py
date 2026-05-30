"""
EkalavyaAI — Cashfree Payment Service
Handles subscription order creation, verification, and webhooks.
"""
import hashlib
import hmac
import json
import logging
from datetime import datetime, timedelta
from typing import Optional

import httpx

from config import settings, SUBSCRIPTION_PLANS

logger = logging.getLogger(__name__)

CASHFREE_BASE = {
    "TEST": "https://sandbox.cashfree.com/pg",
    "PROD": "https://api.cashfree.com/pg",
}


class PaymentService:
    """Cashfree PG integration for EkalavyaAI subscriptions."""

    def __init__(self):
        self.base_url = CASHFREE_BASE.get(settings.CASHFREE_ENV, CASHFREE_BASE["TEST"])
        self.headers = {
            "Content-Type": "application/json",
            "x-api-version": "2023-08-01",
            "x-client-id": settings.CASHFREE_APP_ID,
            "x-client-secret": settings.CASHFREE_SECRET_KEY,
        }

    async def create_order(
        self,
        student_id: str,
        student_email: str,
        student_name: str,
        plan: str,
        is_annual: bool = False,
    ) -> dict:
        """Create a Cashfree payment order for a subscription."""
        plan_config = SUBSCRIPTION_PLANS.get(plan, {})
        amount = plan_config.get("price_annual" if is_annual else "price_monthly", 0)
        if amount == 0:
            raise ValueError("Cannot create payment order for free plan")

        order_id = f"EKA-{student_id[:8].upper()}-{int(datetime.utcnow().timestamp())}"
        payload = {
            "order_id": order_id,
            "order_amount": float(amount),
            "order_currency": "INR",
            "order_note": f"EkalavyaAI {plan} {'Annual' if is_annual else 'Monthly'} Plan",
            "customer_details": {
                "customer_id": student_id,
                "customer_email": student_email,
                "customer_name": student_name,
                "customer_phone": "9999999999",
            },
            "order_meta": {
                "return_url": f"{settings.APP_URL}/payment/success?order_id={{order_id}}",
                "notify_url": f"{settings.API_URL}/api/v1/payments/webhook",
            },
            "order_expiry_time": (
                datetime.utcnow() + timedelta(minutes=30)
            ).strftime("%Y-%m-%dT%H:%M:%S+05:30"),
        }

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/orders",
                headers=self.headers,
                json=payload,
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
            return {
                "order_id": order_id,
                "payment_session_id": data.get("payment_session_id"),
                "order_status": data.get("order_status"),
                "amount": amount,
                "plan": plan,
                "is_annual": is_annual,
            }

    async def verify_payment(self, order_id: str) -> dict:
        """Verify payment status from Cashfree."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.base_url}/orders/{order_id}",
                headers=self.headers,
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
            return {
                "order_id": order_id,
                "paid": data.get("order_status") == "PAID",
                "amount": data.get("order_amount"),
                "payment_id": data.get("cf_order_id"),
            }

    def verify_webhook_signature(self, raw_body: str, timestamp: str, signature: str) -> bool:
        """Verify Cashfree webhook signature."""
        message = f"{timestamp}{raw_body}"
        computed = hmac.new(
            settings.CASHFREE_SECRET_KEY.encode(),
            message.encode(),
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(computed, signature)

    async def activate_subscription(
        self,
        student_id: str,
        plan: str,
        is_annual: bool,
        payment_id: str,
        order_id: str,
        amount_paid: float,
    ):
        """Activate student subscription after verified payment."""
        from models.database import get_async_session
        from models.user import User, Subscription, SubscriptionPlan
        import uuid as _uuid

        async with get_async_session() as session:
            duration_days = 365 if is_annual else 30
            subscription = Subscription(
                student_id=_uuid.UUID(student_id),
                plan=SubscriptionPlan(plan),
                start_date=datetime.utcnow(),
                end_date=datetime.utcnow() + timedelta(days=duration_days),
                payment_id=payment_id,
                cashfree_order_id=order_id,
                status="ACTIVE",
                is_annual=is_annual,
                amount_paid=amount_paid,
            )
            session.add(subscription)

            # Update user plan
            from sqlalchemy import select
            result = await session.execute(
                select(User).where(User.id == _uuid.UUID(student_id))
            )
            user = result.scalar_one_or_none()
            if user:
                user.plan = plan

            await session.commit()
            logger.info(f"Subscription activated: {student_id} -> {plan} ({'annual' if is_annual else 'monthly'})")
