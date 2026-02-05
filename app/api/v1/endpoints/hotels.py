from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from datetime import date

from app.db.session import get_db
from app.models.user import User
from app.schemas.hotel import (
    HotelCreate,
    HotelUpdate,
    HotelResponse,
    HotelListResponse,
    HotelInfoResponse,
)
from app.schemas.room import RoomResponse
from app.services.hotel import HotelService
from app.core.dependencies import get_current_hotel_admin

# Public router for hotel browsing
public_router = APIRouter()

# Admin router for hotel management
admin_router = APIRouter()


# ============ PUBLIC ENDPOINTS ============

@public_router.get("/search", response_model=HotelListResponse)
async def search_hotels(
    city: Optional[str] = Query(None, description="City to search in"),
    check_in_date: Optional[date] = Query(None, description="Check-in date"),
    check_out_date: Optional[date] = Query(None, description="Check-out date"),
    guests: Optional[int] = Query(None, ge=1, description="Number of guests"),
    rooms: Optional[int] = Query(None, ge=1, description="Number of rooms"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price"),
    max_price: Optional[float] = Query(None, description="Maximum price"),
    amenities: Optional[str] = Query(None, description="Comma-separated amenities"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Search for available hotels"""
    hotel_service = HotelService(db)

    amenities_list = amenities.split(",") if amenities else None

    result = await hotel_service.search_hotels(
        city=city,
        check_in_date=check_in_date,
        check_out_date=check_out_date,
        guests=guests,
        rooms=rooms,
        min_price=min_price,
        max_price=max_price,
        amenities=amenities_list,
        page=page,
        page_size=page_size
    )

    return HotelListResponse(**result)


@public_router.get("/{hotel_id}/info", response_model=HotelInfoResponse)
async def get_hotel_info(
    hotel_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get hotel details with rooms for public view"""
    hotel_service = HotelService(db)
    hotel = await hotel_service.get_hotel_info(hotel_id)

    return HotelInfoResponse(
        id=hotel.id,
        owner_id=hotel.owner_id,
        name=hotel.name,
        description=hotel.description,
        city=hotel.city,
        address=hotel.address,
        latitude=hotel.latitude,
        longitude=hotel.longitude,
        amenities=hotel.amenities or [],
        photos=hotel.photos or [],
        contact_email=hotel.contact_email,
        contact_phone=hotel.contact_phone,
        is_active=hotel.is_active,
        rating=hotel.rating,
        total_reviews=hotel.total_reviews,
        created_at=hotel.created_at,
        updated_at=hotel.updated_at,
        rooms=[RoomResponse.model_validate(room) for room in hotel.rooms]
    )


# ============ ADMIN ENDPOINTS ============

@admin_router.post("", response_model=HotelResponse, status_code=status.HTTP_201_CREATED)
async def create_hotel(
    hotel_data: HotelCreate,
    current_user: User = Depends(get_current_hotel_admin),
    db: AsyncSession = Depends(get_db)
):
    """Create a new hotel"""
    hotel_service = HotelService(db)
    return await hotel_service.create_hotel(current_user, hotel_data)


@admin_router.get("", response_model=HotelListResponse)
async def get_admin_hotels(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_hotel_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get all hotels owned by the current admin"""
    hotel_service = HotelService(db)
    result = await hotel_service.get_admin_hotels(current_user, page, page_size)
    return HotelListResponse(**result)


@admin_router.get("/{hotel_id}", response_model=HotelResponse)
async def get_hotel(
    hotel_id: int,
    current_user: User = Depends(get_current_hotel_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get hotel by ID"""
    hotel_service = HotelService(db)
    return await hotel_service.get_hotel_by_id(hotel_id, current_user)


@admin_router.put("/{hotel_id}", response_model=HotelResponse)
async def update_hotel(
    hotel_id: int,
    update_data: HotelUpdate,
    current_user: User = Depends(get_current_hotel_admin),
    db: AsyncSession = Depends(get_db)
):
    """Update hotel details"""
    hotel_service = HotelService(db)
    return await hotel_service.update_hotel(hotel_id, current_user, update_data)


@admin_router.delete("/{hotel_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_hotel(
    hotel_id: int,
    current_user: User = Depends(get_current_hotel_admin),
    db: AsyncSession = Depends(get_db)
):
    """Delete a hotel"""
    hotel_service = HotelService(db)
    await hotel_service.delete_hotel(hotel_id, current_user)
    return None


@admin_router.patch("/{hotel_id}/activate", response_model=HotelResponse)
async def activate_hotel(
    hotel_id: int,
    current_user: User = Depends(get_current_hotel_admin),
    db: AsyncSession = Depends(get_db)
):
    """Activate a hotel (make it visible for booking)"""
    hotel_service = HotelService(db)
    return await hotel_service.activate_hotel(hotel_id, current_user)


@admin_router.patch("/{hotel_id}/deactivate", response_model=HotelResponse)
async def deactivate_hotel(
    hotel_id: int,
    current_user: User = Depends(get_current_hotel_admin),
    db: AsyncSession = Depends(get_db)
):
    """Deactivate a hotel"""
    hotel_service = HotelService(db)
    return await hotel_service.deactivate_hotel(hotel_id, current_user)
