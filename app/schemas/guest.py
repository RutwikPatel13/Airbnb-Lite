from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from app.models.guest import Gender


class GuestBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    gender: Optional[Gender] = None
    age: Optional[int] = Field(None, ge=0, le=150)


class GuestCreate(GuestBase):
    pass


class GuestUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    gender: Optional[Gender] = None
    age: Optional[int] = Field(None, ge=0, le=150)


class GuestResponse(GuestBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class GuestListResponse(BaseModel):
    guests: List[GuestResponse]
    total: int
