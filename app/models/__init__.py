# Import all models for Alembic to detect
from app.models.user import User, UserRole
from app.models.guest import Guest, Gender, booking_guests
from app.models.hotel import Hotel
from app.models.room import Room, RoomType
from app.models.inventory import Inventory
from app.models.booking import Booking, BookingStatus
from app.models.payment import Payment, PaymentStatus, PaymentMethod

__all__ = [
    "User",
    "UserRole",
    "Guest",
    "Gender",
    "booking_guests",
    "Hotel",
    "Room",
    "RoomType",
    "Inventory",
    "Booking",
    "BookingStatus",
    "Payment",
    "PaymentStatus",
    "PaymentMethod",
]
