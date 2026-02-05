from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.models.payment import PaymentStatus, PaymentMethod


class PaymentInitiate(BaseModel):
    """Initiate payment for a booking"""
    payment_method: PaymentMethod


class PaymentResponse(BaseModel):
    id: int
    booking_id: int
    amount: float
    currency: str
    status: PaymentStatus
    payment_method: Optional[PaymentMethod] = None
    transaction_id: Optional[str] = None
    payment_session_id: Optional[str] = None
    paid_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PaymentWebhookPayload(BaseModel):
    """Webhook payload from payment gateway (mock)"""
    payment_session_id: str
    transaction_id: str
    status: str  # "success" or "failed"
    amount: float
    currency: str = "USD"


class PaymentSessionResponse(BaseModel):
    """Response when initiating payment"""
    payment_session_id: str
    payment_url: str  # Mock URL for payment
    amount: float
    currency: str
    expires_at: datetime
