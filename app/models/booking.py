from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Date, Float, Enum as SQLEnum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base
from app.models.guest import booking_guests
import enum


class BookingStatus(str, enum.Enum):
    PENDING = "PENDING"  # Initial state, awaiting payment
    CONFIRMED = "CONFIRMED"  # Payment successful
    CANCELLED = "CANCELLED"  # Cancelled by user or system
    CHECKED_IN = "CHECKED_IN"  # Guest has checked in
    CHECKED_OUT = "CHECKED_OUT"  # Guest has checked out
    EXPIRED = "EXPIRED"  # Payment not completed in time


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    hotel_id = Column(Integer, ForeignKey("hotels.id", ondelete="CASCADE"), nullable=False)
    room_id = Column(Integer, ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False)

    check_in_date = Column(Date, nullable=False, index=True)
    check_out_date = Column(Date, nullable=False, index=True)
    rooms_count = Column(Integer, nullable=False, default=1)  # Number of rooms booked

    total_price = Column(Float, nullable=False)
    status = Column(SQLEnum(BookingStatus), default=BookingStatus.PENDING, nullable=False)

    special_requests = Column(Text, nullable=True)
    cancellation_reason = Column(Text, nullable=True)

    # Payment tracking
    payment_session_id = Column(String(255), nullable=True)  # For payment gateway reference

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="bookings")
    hotel = relationship("Hotel", back_populates="bookings")
    room = relationship("Room", back_populates="bookings")
    guests = relationship("Guest", secondary=booking_guests, back_populates="bookings")
    payment = relationship("Payment", back_populates="booking", uselist=False, cascade="all, delete-orphan")

    @property
    def nights(self) -> int:
        """Calculate number of nights"""
        return (self.check_out_date - self.check_in_date).days

    def __repr__(self):
        return f"<Booking(id={self.id}, status={self.status}, hotel_id={self.hotel_id})>"
