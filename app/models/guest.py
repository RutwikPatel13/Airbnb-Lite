from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum as SQLEnum, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base
import enum


class Gender(str, enum.Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"
    OTHER = "OTHER"


# Association table for booking-guest many-to-many relationship
booking_guests = Table(
    "booking_guests",
    Base.metadata,
    Column("booking_id", Integer, ForeignKey("bookings.id", ondelete="CASCADE"), primary_key=True),
    Column("guest_id", Integer, ForeignKey("guests.id", ondelete="CASCADE"), primary_key=True)
)


class Guest(Base):
    __tablename__ = "guests"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)
    gender = Column(SQLEnum(Gender), nullable=True)
    age = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="guests")
    bookings = relationship("Booking", secondary=booking_guests, back_populates="guests")

    def __repr__(self):
        return f"<Guest(id={self.id}, name={self.name})>"
