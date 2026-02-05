from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float, JSON, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base
import enum


class RoomType(str, enum.Enum):
    SINGLE = "SINGLE"
    DOUBLE = "DOUBLE"
    DELUXE = "DELUXE"
    SUITE = "SUITE"
    PENTHOUSE = "PENTHOUSE"


class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    hotel_id = Column(Integer, ForeignKey("hotels.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    room_type = Column(SQLEnum(RoomType), nullable=False)
    base_price = Column(Float, nullable=False)
    total_count = Column(Integer, nullable=False, default=1)  # Total rooms of this type
    capacity = Column(Integer, nullable=False, default=2)  # Max guests
    amenities = Column(JSON, default=list)
    photos = Column(JSON, default=list)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    hotel = relationship("Hotel", back_populates="rooms")
    inventories = relationship("Inventory", back_populates="room", cascade="all, delete-orphan")
    bookings = relationship("Booking", back_populates="room", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Room(id={self.id}, name={self.name}, type={self.room_type})>"
