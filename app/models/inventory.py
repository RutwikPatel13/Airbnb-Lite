from sqlalchemy import Column, Integer, ForeignKey, DateTime, Date, Float, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base


class Inventory(Base):
    """
    Tracks room availability and pricing for each date.
    Each record represents availability for a specific room type on a specific date.
    """
    __tablename__ = "inventories"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=False, index=True)
    available_count = Column(Integer, nullable=False)  # Rooms available on this date
    booked_count = Column(Integer, default=0)  # Rooms booked on this date
    price = Column(Float, nullable=False)  # Price for this date (can vary)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Unique constraint: one inventory record per room per date
    __table_args__ = (
        UniqueConstraint('room_id', 'date', name='uq_room_date'),
    )

    # Relationships
    room = relationship("Room", back_populates="inventories")

    @property
    def remaining_count(self) -> int:
        """Calculate remaining available rooms"""
        return self.available_count - self.booked_count

    def __repr__(self):
        return f"<Inventory(room_id={self.room_id}, date={self.date}, available={self.remaining_count})>"
