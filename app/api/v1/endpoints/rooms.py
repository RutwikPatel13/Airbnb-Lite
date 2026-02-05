from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User
from app.schemas.room import RoomCreate, RoomUpdate, RoomResponse, RoomListResponse
from app.services.room import RoomService
from app.core.dependencies import get_current_hotel_admin

router = APIRouter()


@router.post("/{hotel_id}/rooms", response_model=RoomResponse, status_code=status.HTTP_201_CREATED)
async def create_room(
    hotel_id: int,
    room_data: RoomCreate,
    current_user: User = Depends(get_current_hotel_admin),
    db: AsyncSession = Depends(get_db)
):
    """Create a new room for a hotel"""
    room_service = RoomService(db)
    return await room_service.create_room(hotel_id, current_user, room_data)


@router.get("/{hotel_id}/rooms", response_model=RoomListResponse)
async def get_rooms(
    hotel_id: int,
    current_user: User = Depends(get_current_hotel_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get all rooms for a hotel"""
    room_service = RoomService(db)
    rooms = await room_service.get_rooms(hotel_id, current_user)
    return RoomListResponse(rooms=rooms, total=len(rooms))


@router.get("/{hotel_id}/rooms/{room_id}", response_model=RoomResponse)
async def get_room(
    hotel_id: int,
    room_id: int,
    current_user: User = Depends(get_current_hotel_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific room by ID"""
    room_service = RoomService(db)
    return await room_service.get_room_by_id(hotel_id, room_id, current_user)


@router.put("/{hotel_id}/rooms/{room_id}", response_model=RoomResponse)
async def update_room(
    hotel_id: int,
    room_id: int,
    update_data: RoomUpdate,
    current_user: User = Depends(get_current_hotel_admin),
    db: AsyncSession = Depends(get_db)
):
    """Update a room"""
    room_service = RoomService(db)
    return await room_service.update_room(hotel_id, room_id, current_user, update_data)


@router.delete("/{hotel_id}/rooms/{room_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_room(
    hotel_id: int,
    room_id: int,
    current_user: User = Depends(get_current_hotel_admin),
    db: AsyncSession = Depends(get_db)
):
    """Delete a room"""
    room_service = RoomService(db)
    await room_service.delete_room(hotel_id, room_id, current_user)
    return None
