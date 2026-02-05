from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate
from app.schemas.booking import BookingListResponse, BookingDetailResponse
from app.services.user import UserService
from app.core.dependencies import get_current_active_user

router = APIRouter()


@router.get("/profile", response_model=UserResponse)
async def get_my_profile(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current user's profile"""
    user_service = UserService(db)
    return await user_service.get_profile(current_user)


@router.patch("/profile", response_model=UserResponse)
async def update_my_profile(
    update_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update current user's profile"""
    user_service = UserService(db)
    return await user_service.update_profile(current_user, update_data)


@router.get("/myBookings", response_model=BookingListResponse)
async def get_my_bookings(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current user's bookings"""
    user_service = UserService(db)
    result = await user_service.get_my_bookings(current_user, page, page_size)

    # Transform bookings to include hotel and room names
    bookings_with_details = []
    for booking in result["bookings"]:
        booking_dict = BookingDetailResponse(
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
            guests=booking.guests,
            hotel_name=booking.hotel.name if booking.hotel else None,
            room_name=booking.room.name if booking.room else None,
        )
        bookings_with_details.append(booking_dict)

    return BookingListResponse(
        bookings=bookings_with_details,
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"]
    )
