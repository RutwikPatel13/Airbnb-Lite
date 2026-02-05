from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User
from app.schemas.payment import (
    PaymentInitiate,
    PaymentResponse,
    PaymentSessionResponse,
    PaymentWebhookPayload,
)
from app.services.payment import PaymentService
from app.core.dependencies import get_current_active_user

router = APIRouter()


# ============ WEBHOOK ENDPOINTS ============

@router.post("/payment/capture")
async def capture_payment(
    webhook_data: PaymentWebhookPayload,
    db: AsyncSession = Depends(get_db)
):
    """
    Webhook endpoint to capture payment notification from payment gateway.
    This would typically be called by the payment provider (e.g., Stripe, Razorpay)
    after a payment is processed.

    For mock purposes, you can call this endpoint manually to simulate payment completion.
    """
    payment_service = PaymentService(db)
    return await payment_service.process_webhook(webhook_data)


# ============ PAYMENT ENDPOINTS ============
# These are placed in webhooks.py as they relate to payments

@router.post("/bookings/{booking_id}/pay", response_model=PaymentSessionResponse)
async def initiate_payment(
    booking_id: int,
    payment_data: PaymentInitiate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Initiate payment for a booking.
    Returns a mock payment URL and session ID.
    """
    payment_service = PaymentService(db)
    return await payment_service.initiate_payment(booking_id, current_user, payment_data)


@router.get("/bookings/{booking_id}/payment", response_model=PaymentResponse)
async def get_payment(
    booking_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get payment details for a booking"""
    payment_service = PaymentService(db)
    return await payment_service.get_payment_by_booking(booking_id, current_user)
