from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status
from typing import List

from app.models.guest import Guest
from app.models.user import User
from app.schemas.guest import GuestCreate, GuestUpdate


class GuestService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_guest(self, user: User, guest_data: GuestCreate) -> Guest:
        """Create a new guest for the user"""
        guest = Guest(
            user_id=user.id,
            name=guest_data.name,
            email=guest_data.email,
            phone=guest_data.phone,
            gender=guest_data.gender,
            age=guest_data.age,
        )

        self.db.add(guest)
        await self.db.flush()
        await self.db.refresh(guest)

        return guest

    async def get_guests(self, user: User) -> List[Guest]:
        """Get all guests for the user"""
        result = await self.db.execute(
            select(Guest)
            .where(Guest.user_id == user.id)
            .order_by(Guest.created_at.desc())
        )
        return result.scalars().all()

    async def get_guest_by_id(self, user: User, guest_id: int) -> Guest:
        """Get a specific guest by ID"""
        result = await self.db.execute(
            select(Guest)
            .where(Guest.id == guest_id, Guest.user_id == user.id)
        )
        guest = result.scalar_one_or_none()

        if not guest:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Guest not found"
            )

        return guest

    async def update_guest(
        self,
        user: User,
        guest_id: int,
        update_data: GuestUpdate
    ) -> Guest:
        """Update a guest"""
        guest = await self.get_guest_by_id(user, guest_id)

        update_dict = update_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(guest, field, value)

        await self.db.flush()
        await self.db.refresh(guest)

        return guest

    async def delete_guest(self, user: User, guest_id: int) -> None:
        """Delete a guest"""
        guest = await self.get_guest_by_id(user, guest_id)
        await self.db.delete(guest)
        await self.db.flush()

    async def get_guests_by_ids(self, user: User, guest_ids: List[int]) -> List[Guest]:
        """Get multiple guests by IDs (for booking)"""
        result = await self.db.execute(
            select(Guest)
            .where(Guest.id.in_(guest_ids), Guest.user_id == user.id)
        )
        guests = result.scalars().all()

        if len(guests) != len(guest_ids):
            found_ids = {g.id for g in guests}
            missing_ids = set(guest_ids) - found_ids
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Guests not found: {missing_ids}"
            )

        return guests
