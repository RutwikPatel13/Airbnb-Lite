from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.models.room import RoomType


class RoomBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    room_type: RoomType
    base_price: float = Field(..., gt=0)
    total_count: int = Field(..., ge=1)
    capacity: int = Field(..., ge=1)
    amenities: List[str] = []
    photos: List[str] = []


class RoomCreate(RoomBase):
    pass


class RoomUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    room_type: Optional[RoomType] = None
    base_price: Optional[float] = Field(None, gt=0)
    total_count: Optional[int] = Field(None, ge=1)
    capacity: Optional[int] = Field(None, ge=1)
    amenities: Optional[List[str]] = None
    photos: Optional[List[str]] = None


class RoomResponse(RoomBase):
    id: int
    hotel_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RoomListResponse(BaseModel):
    rooms: List[RoomResponse]
    total: int


class RoomAvailabilityResponse(RoomResponse):
    """Room with availability info for a date range"""
    available_count: int = 0
    price_per_night: float = 0.0
    total_price: float = 0.0
