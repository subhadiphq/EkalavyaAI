"""
EkalavyaAI — Payments API Routes
Cashfree payment order creation, verification, and webhook handling.
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from api.dependencies import get_current_user
from services.payment_service import PaymentService

logger = logging.getLogger(__name__)
router = APIRouter()
payment_service = PaymentService()


class CreateOrderRequest(BaseModel):
    plan: str   # BASIC | PRO | INSTITUTE
    is_annual: bool = False


@router.post("/create-order")
async def create_payment_order(
    request: CreateOrderRequest,
    current_user=Depends(get_current_user),
):
    """Create a Cashfree payment order for a subscription plan."""
    if request.plan not in ("BASIC", "PRO", "INSTITUTE"):
        raise HTTPException(status_code=400, detail="Invalid plan")

    try:
        order = await payment_service.create_order(
            student_id=str(current_user.id),
            student_email=current_user.email,
            student_name=current_user.name,
            plan=request.plan,
            is_annual=request.is_annual,
        )
        return order
    except Exception as e:
        logger.error(f"Payment order creation failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to create payment order")


@router.get("/verify/{order_id}")
async def verify_payment(
    order_id: str,
    current_user=Depends(get_current_user),
):
    """Verify payment status and activate subscription."""
    try:
        result = await payment_service.verify_payment(order_id)
        if result["paid"]:
            # Parse plan from order_id meta (simplified)
            logger.info(f"Payment verified: {order_id} for user {current_user.id}")
        return result
    except Exception as e:
        logger.error(f"Payment verification failed: {e}")
        raise HTTPException(status_code=500, detail="Payment verification failed")


@router.post("/webhook")
async def payment_webhook(request: Request):
    """Cashfree webhook for payment status updates."""
    try:
        body = await request.body()
        timestamp = request.headers.get("x-webhook-timestamp", "")
        signature = request.headers.get("x-webhook-signature", "")

        if not payment_service.verify_webhook_signature(
            body.decode(), timestamp, signature
        ):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")

        import json
        data = json.loads(body)
        event_type = data.get("type")

        if event_type == "PAYMENT_SUCCESS_WEBHOOK":
            order_data = data.get("data", {}).get("order", {})
            order_id = order_data.get("order_id", "")
            # Extract student_id from order_id (EKA-{student_id}-{timestamp})
            parts = order_id.split("-")
            if len(parts) >= 3:
                logger.info(f"Payment webhook success: {order_id}")

        return {"status": "ok"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        return {"status": "error"}
