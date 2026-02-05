from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime
from app.models.booking import BookingStatus
from app.schemas.guest import GuestResponse


class BookingBase(BaseModel):
    hotel_id: int
    room_id: int
    check_in_date: date
    check_out_date: date
    rooms_count: int = Field(1, ge=1)
    special_requests: Optional[str] = None


class BookingCreate(BookingBase):
    """Initialize a new booking"""
    pass


class BookingAddGuests(BaseModel):
    """Add guests to a booking"""
    guest_ids: List[int]


class BookingCancel(BaseModel):
    """Cancel a booking"""
    reason: Optional[str] = None


class BookingResponse(BookingBase):
    id: int
    user_id: int
    total_price: float
    status: BookingStatus
    cancellation_reason: Optional[str] = None
    payment_session_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BookingDetailResponse(BookingResponse):
    """Booking with guest details"""
    guests: List[GuestResponse] = []
    hotel_name: Optional[str] = None
    room_name: Optional[str] = None


class BookingListResponse(BaseModel):
    bookings: List[BookingDetailResponse]
    total: int
    page: int
    page_size: int


class BookingStatusResponse(BaseModel):
    booking_id: int
    status: BookingStatus
    payment_status: Optional[str] = None


class HotelBookingReport(BaseModel):
    """Report for hotel bookings"""
    hotel_id: int
    hotel_name: str
    total_bookings: int
    confirmed_bookings: int
    cancelled_bookings: int
    pending_bookings: int
    total_revenue: float
    average_booking_value: float
    occupancy_rate: float
    report_period_start: date
    report_period_end: date
