from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime


class InventoryBase(BaseModel):
    date: date
    available_count: int = Field(..., ge=0)
    price: float = Field(..., gt=0)


class InventoryCreate(InventoryBase):
    room_id: int


class InventoryUpdate(BaseModel):
    available_count: Optional[int] = Field(None, ge=0)
    price: Optional[float] = Field(None, gt=0)


class InventoryBulkUpdate(BaseModel):
    """Update inventory for a date range"""
    start_date: date
    end_date: date
    available_count: Optional[int] = Field(None, ge=0)
    price: Optional[float] = Field(None, gt=0)


class InventoryResponse(InventoryBase):
    id: int
    room_id: int
    booked_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

    @property
    def remaining_count(self) -> int:
        return self.available_count - self.booked_count


class InventoryListResponse(BaseModel):
    inventories: List[InventoryResponse]
    room_id: int
    total: int
