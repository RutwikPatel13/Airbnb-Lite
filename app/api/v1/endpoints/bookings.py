from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import date

from app.db.session import get_db
from app.models.user import User
from app.models.booking import BookingStatus
from app.schemas.booking import (
    BookingCreate,
    BookingAddGuests,
    BookingCancel,
    BookingResponse,
    BookingDetailResponse,
    BookingListResponse,
    BookingStatusResponse,
    HotelBookingReport,
)
from app.schemas.guest import GuestResponse
from app.services.booking import BookingService
from app.core.dependencies import get_current_active_user, get_current_hotel_admin

# Public router for user bookings
router = APIRouter()

# Admin router for hotel booking management
admin_router = APIRouter()


# ============ USER BOOKING ENDPOINTS ============

@router.post("/init", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
async def init_booking(
    booking_data: BookingCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Initialize a new booking"""
    booking_service = BookingService(db)
    return await booking_service.init_booking(current_user, booking_data)


@router.post("/{booking_id}/addGuests", response_model=BookingDetailResponse)
async def add_guests_to_booking(
    booking_id: int,
    guest_data: BookingAddGuests,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Add guests to a booking"""
    booking_service = BookingService(db)
    booking = await booking_service.add_guests_to_booking(booking_id, current_user, guest_data)

    return BookingDetailResponse(
        id=booking.id,
        user_id=booking.user_id,
        hotel_id=booking.hotel_id,
        room_id=booking.room_id,
        check_in_date=booking.check_in_date,
        check_out_date=booking.check_out_date,
        rooms_count=booking.rooms_count,
        total_price=booking.total_price,
        status=booking.status,
        special_requests=booking.special_requests,
        cancellation_reason=booking.cancellation_reason,
        payment_session_id=booking.payment_session_id,
        created_at=booking.created_at,
        updated_at=booking.updated_at,
        guests=[GuestResponse.model_validate(g) for g in booking.guests],
        hotel_name=booking.hotel.name if booking.hotel else None,
        room_name=booking.room.name if booking.room else None
    )


@router.get("/{booking_id}/status", response_model=BookingStatusResponse)
async def get_booking_status(
    booking_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get booking status"""
    booking_service = BookingService(db)
    return await booking_service.get_booking_status(booking_id, current_user)


@router.post("/{booking_id}/cancel", response_model=BookingResponse)
async def cancel_booking(
    booking_id: int,
    cancel_data: BookingCancel,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Cancel a booking"""
    booking_service = BookingService(db)
    return await booking_service.cancel_booking(booking_id, current_user, cancel_data)


# ============ ADMIN BOOKING ENDPOINTS ============

@admin_router.get("/{hotel_id}/bookings", response_model=BookingListResponse)
async def get_hotel_bookings(
    hotel_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    status_filter: Optional[BookingStatus] = Query(None, description="Filter by status"),
    current_user: User = Depends(get_current_hotel_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get all bookings for a hotel (admin)"""
    booking_service = BookingService(db)
    result = await booking_service.get_hotel_bookings(
        hotel_id, current_user, page, page_size, status_filter
    )

    bookings_response = [
        BookingDetailResponse(
            id=b.id,
            user_id=b.user_id,
            hotel_id=b.hotel_id,
            room_id=b.room_id,
            check_in_date=b.check_in_date,
            check_out_date=b.check_out_date,
            rooms_count=b.rooms_count,
            total_price=b.total_price,
            status=b.status,
            special_requests=b.special_requests,
            cancellation_reason=b.cancellation_reason,
            payment_session_id=b.payment_session_id,
            created_at=b.created_at,
            updated_at=b.updated_at,
            guests=[GuestResponse.model_validate(g) for g in b.guests],
            hotel_name=None,
            room_name=b.room.name if b.room else None
        )
        for b in result["bookings"]
    ]

    return BookingListResponse(
        bookings=bookings_response,
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"]
    )


@admin_router.get("/{hotel_id}/reports", response_model=HotelBookingReport)
async def get_hotel_report(
    hotel_id: int,
    start_date: Optional[date] = Query(None, description="Report start date"),
    end_date: Optional[date] = Query(None, description="Report end date"),
    current_user: User = Depends(get_current_hotel_admin),
    db: AsyncSession = Depends(get_db)
):
    """Generate booking report for a hotel (admin)"""
    booking_service = BookingService(db)
    return await booking_service.get_hotel_report(hotel_id, current_user, start_date, end_date)
