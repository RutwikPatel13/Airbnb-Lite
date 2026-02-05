from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from fastapi import HTTPException, status
from typing import List, Optional
from datetime import date, timedelta

from app.models.inventory import Inventory
from app.models.room import Room
from app.models.hotel import Hotel
from app.models.user import User, UserRole
from app.schemas.inventory import InventoryUpdate, InventoryBulkUpdate


class InventoryService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _verify_room_access(self, room_id: int, user: User) -> Room:
        """Verify user has access to the room's hotel"""
        result = await self.db.execute(
            select(Room).where(Room.id == room_id)
        )
        room = result.scalar_one_or_none()

        if not room:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Room not found"
            )

        # Get hotel to check ownership
        hotel_result = await self.db.execute(
            select(Hotel).where(Hotel.id == room.hotel_id)
        )
        hotel = hotel_result.scalar_one_or_none()

        if user.role != UserRole.ADMIN and hotel.owner_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this room's inventory"
            )

        return room

    async def get_room_inventory(
        self,
        room_id: int,
        user: User,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[Inventory]:
        """Get inventory for a room within a date range"""
        await self._verify_room_access(room_id, user)

        if not start_date:
            start_date = date.today()
        if not end_date:
            end_date = start_date + timedelta(days=30)

        result = await self.db.execute(
            select(Inventory)
            .where(
                Inventory.room_id == room_id,
                Inventory.date >= start_date,
                Inventory.date <= end_date
            )
            .order_by(Inventory.date)
        )
        return result.scalars().all()

    async def update_inventory(
        self,
        room_id: int,
        inv_date: date,
        user: User,
        update_data: InventoryUpdate
    ) -> Inventory:
        """Update inventory for a specific date"""
        await self._verify_room_access(room_id, user)

        result = await self.db.execute(
            select(Inventory)
            .where(Inventory.room_id == room_id, Inventory.date == inv_date)
        )
        inventory = result.scalar_one_or_none()

        if not inventory:
            # Create new inventory record if it doesn't exist
            room = await self._verify_room_access(room_id, user)
            inventory = Inventory(
                room_id=room_id,
                date=inv_date,
                available_count=update_data.available_count or room.total_count,
                booked_count=0,
                price=update_data.price or room.base_price,
            )
            self.db.add(inventory)
        else:
            update_dict = update_data.model_dump(exclude_unset=True)
            for field, value in update_dict.items():
                setattr(inventory, field, value)

        await self.db.flush()
        await self.db.refresh(inventory)

        return inventory

    async def bulk_update_inventory(
        self,
        room_id: int,
        user: User,
        bulk_data: InventoryBulkUpdate
    ) -> List[Inventory]:
        """Update inventory for a date range"""
        room = await self._verify_room_access(room_id, user)

        if bulk_data.start_date > bulk_data.end_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Start date must be before end date"
            )

        updated_inventories = []
        current_date = bulk_data.start_date

        while current_date <= bulk_data.end_date:
            result = await self.db.execute(
                select(Inventory)
                .where(Inventory.room_id == room_id, Inventory.date == current_date)
            )
            inventory = result.scalar_one_or_none()

            if not inventory:
                inventory = Inventory(
                    room_id=room_id,
                    date=current_date,
                    available_count=bulk_data.available_count or room.total_count,
                    booked_count=0,
                    price=bulk_data.price or room.base_price,
                )
                self.db.add(inventory)
            else:
                if bulk_data.available_count is not None:
                    inventory.available_count = bulk_data.available_count
                if bulk_data.price is not None:
                    inventory.price = bulk_data.price

            updated_inventories.append(inventory)
            current_date += timedelta(days=1)

        await self.db.flush()

        # Refresh all inventories
        for inv in updated_inventories:
            await self.db.refresh(inv)

        return updated_inventories
