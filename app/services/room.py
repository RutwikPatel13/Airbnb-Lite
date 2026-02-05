from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import HTTPException, status
from typing import List
from datetime import date, timedelta

from app.models.room import Room
from app.models.hotel import Hotel
from app.models.inventory import Inventory
from app.models.user import User, UserRole
from app.schemas.room import RoomCreate, RoomUpdate


class RoomService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _verify_hotel_access(self, hotel_id: int, user: User) -> Hotel:
        """Verify user has access to the hotel"""
        result = await self.db.execute(
            select(Hotel).where(Hotel.id == hotel_id)
        )
        hotel = result.scalar_one_or_none()

        if not hotel:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Hotel not found"
            )

        if user.role != UserRole.ADMIN and hotel.owner_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this hotel"
            )

        return hotel

    async def create_room(
        self,
        hotel_id: int,
        user: User,
        room_data: RoomCreate
    ) -> Room:
        """Create a new room for a hotel"""
        await self._verify_hotel_access(hotel_id, user)

        room = Room(
            hotel_id=hotel_id,
            name=room_data.name,
            description=room_data.description,
            room_type=room_data.room_type,
            base_price=room_data.base_price,
            total_count=room_data.total_count,
            capacity=room_data.capacity,
            amenities=room_data.amenities,
            photos=room_data.photos,
        )

        self.db.add(room)
        await self.db.flush()
        await self.db.refresh(room)

        # Initialize inventory for the next 90 days
        await self._initialize_inventory(room)

        return room

    async def _initialize_inventory(self, room: Room, days: int = 90):
        """Initialize inventory for a room for the next N days"""
        today = date.today()
        inventories = []

        for i in range(days):
            inv_date = today + timedelta(days=i)
            inventory = Inventory(
                room_id=room.id,
                date=inv_date,
                available_count=room.total_count,
                booked_count=0,
                price=room.base_price,
            )
            inventories.append(inventory)

        self.db.add_all(inventories)
        await self.db.flush()

    async def get_rooms(self, hotel_id: int, user: User) -> List[Room]:
        """Get all rooms for a hotel"""
        await self._verify_hotel_access(hotel_id, user)

        result = await self.db.execute(
            select(Room)
            .where(Room.hotel_id == hotel_id)
            .order_by(Room.created_at.desc())
        )
        return result.scalars().all()

    async def get_room_by_id(
        self,
        hotel_id: int,
        room_id: int,
        user: User
    ) -> Room:
        """Get a specific room by ID"""
        await self._verify_hotel_access(hotel_id, user)

        result = await self.db.execute(
            select(Room)
            .where(Room.id == room_id, Room.hotel_id == hotel_id)
        )
        room = result.scalar_one_or_none()

        if not room:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Room not found"
            )

        return room

    async def update_room(
        self,
        hotel_id: int,
        room_id: int,
        user: User,
        update_data: RoomUpdate
    ) -> Room:
        """Update a room"""
        room = await self.get_room_by_id(hotel_id, room_id, user)

        update_dict = update_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(room, field, value)

        await self.db.flush()
        await self.db.refresh(room)

        return room

    async def delete_room(
        self,
        hotel_id: int,
        room_id: int,
        user: User
    ) -> None:
        """Delete a room"""
        room = await self.get_room_by_id(hotel_id, room_id, user)
        await self.db.delete(room)
        await self.db.flush()
