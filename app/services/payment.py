import uuid
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from app.models.payment import Payment, PaymentStatus, PaymentMethod
from app.models.booking import Booking, BookingStatus
from app.models.user import User
from app.schemas.payment import PaymentInitiate


class PaymentService:
    def __init__(self, db: AsyncSession):
        self.db = db
        # Mock payment gateway URL
        self.payment_gateway_url = "https://mock-payment.airbnblite.com/pay"

    async def initiate_payment(
        self,
        booking_id: int,
        user: User,
        payment_data: PaymentInitiate
    ):
        """Initiate payment for a booking"""
        # Get booking
        result = await self.db.execute(
            select(Booking).where(Booking.id == booking_id)
        )
        booking = result.scalar_one_or_none()

        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Booking not found"
            )

        if booking.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to pay for this booking"
            )

        if booking.status != BookingStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Booking is not in pending status"
            )

        # Check if payment already exists
        payment_result = await self.db.execute(
            select(Payment).where(Payment.booking_id == booking_id)
        )
        existing_payment = payment_result.scalar_one_or_none()

        if existing_payment:
            if existing_payment.status == PaymentStatus.COMPLETED:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Payment already completed"
                )
            # Return existing payment session if still pending
            if existing_payment.status == PaymentStatus.PENDING:
                return {
                    "payment_session_id": existing_payment.payment_session_id,
                    "payment_url": f"{self.payment_gateway_url}/{existing_payment.payment_session_id}",
                    "amount": existing_payment.amount,
                    "currency": existing_payment.currency,
                    "expires_at": existing_payment.created_at + timedelta(minutes=30)
                }

        # Generate mock payment session
        payment_session_id = f"pay_session_{uuid.uuid4().hex[:16]}"

        # Create payment record
        payment = Payment(
            booking_id=booking_id,
            amount=booking.total_price,
            currency="USD",
            status=PaymentStatus.PENDING,
            payment_method=payment_data.payment_method,
            payment_session_id=payment_session_id,
        )

        self.db.add(payment)

        # Update booking with payment session ID
        booking.payment_session_id = payment_session_id

        await self.db.flush()
        await self.db.refresh(payment)

        return {
            "payment_session_id": payment_session_id,
            "payment_url": f"{self.payment_gateway_url}/{payment_session_id}",
            "amount": payment.amount,
            "currency": payment.currency,
            "expires_at": datetime.utcnow() + timedelta(minutes=30)
        }

    async def process_webhook(self, webhook_data):
        """Process payment webhook from payment gateway"""
        # Find payment by session ID
        result = await self.db.execute(
            select(Payment).where(Payment.payment_session_id == webhook_data.payment_session_id)
        )
        payment = result.scalar_one_or_none()

        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment session not found"
            )

        if payment.status != PaymentStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payment already processed"
            )

        # Get booking
        booking_result = await self.db.execute(
            select(Booking).where(Booking.id == payment.booking_id)
        )
        booking = booking_result.scalar_one_or_none()

        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Booking not found"
            )

        if webhook_data.status == "success":
            # Update payment status
            payment.status = PaymentStatus.COMPLETED
            payment.transaction_id = webhook_data.transaction_id
            payment.paid_at = datetime.utcnow()

            # Update booking status to CONFIRMED
            booking.status = BookingStatus.CONFIRMED

            await self.db.flush()
            await self.db.refresh(payment)
            await self.db.refresh(booking)

            return {
                "message": "Payment successful",
                "payment_id": payment.id,
                "booking_id": booking.id,
                "booking_status": booking.status.value,
                "payment_status": payment.status.value
            }
        else:
            # Payment failed
            payment.status = PaymentStatus.FAILED
            payment.transaction_id = webhook_data.transaction_id

            # Keep booking in pending, or you could expire it
            booking.status = BookingStatus.EXPIRED

            await self.db.flush()
            await self.db.refresh(payment)
            await self.db.refresh(booking)

            return {
                "message": "Payment failed",
                "payment_id": payment.id,
                "booking_id": booking.id,
                "booking_status": booking.status.value,
                "payment_status": payment.status.value
            }

    async def get_payment_by_booking(self, booking_id: int, user: User) -> Payment:
        """Get payment details for a booking"""
        # Get booking first to verify access
        booking_result = await self.db.execute(
            select(Booking).where(Booking.id == booking_id)
        )
        booking = booking_result.scalar_one_or_none()

        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Booking not found"
            )

        if booking.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this payment"
            )

        result = await self.db.execute(
            select(Payment).where(Payment.booking_id == booking_id)
        )
        payment = result.scalar_one_or_none()

        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found for this booking"
            )

        return payment
