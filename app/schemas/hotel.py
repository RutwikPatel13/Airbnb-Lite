from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime


class HotelBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    city: str = Field(..., min_length=1, max_length=100)
    address: Optional[str] = Field(None, max_length=500)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    amenities: List[str] = []
    photos: List[str] = []
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = Field(None, max_length=20)


class HotelCreate(HotelBase):
    pass


class HotelUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    city: Optional[str] = Field(None, min_length=1, max_length=100)
    address: Optional[str] = Field(None, max_length=500)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    amenities: Optional[List[str]] = None
    photos: Optional[List[str]] = None
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = Field(None, max_length=20)


class HotelResponse(HotelBase):
    id: int
    owner_id: int
    is_active: bool
    rating: float
    total_reviews: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class HotelListResponse(BaseModel):
    hotels: List[HotelResponse]
    total: int
    page: int
    page_size: int


class HotelSearchParams(BaseModel):
    city: Optional[str] = None
    check_in_date: Optional[str] = None  # YYYY-MM-DD
    check_out_date: Optional[str] = None  # YYYY-MM-DD
    guests: Optional[int] = Field(None, ge=1)
    rooms: Optional[int] = Field(None, ge=1)
    min_price: Optional[float] = Field(None, ge=0)
    max_price: Optional[float] = None
    amenities: Optional[List[str]] = None
    page: int = Field(1, ge=1)
    page_size: int = Field(10, ge=1, le=100)


class HotelInfoResponse(HotelResponse):
    """Extended hotel info with rooms for public view"""
    rooms: List["RoomResponse"] = []


# Import at the end to avoid circular imports
from app.schemas.room import RoomResponse
HotelInfoResponse.model_rebuild()
