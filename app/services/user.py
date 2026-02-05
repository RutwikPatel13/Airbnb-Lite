from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.models.user import User
from app.models.booking import Booking
from app.schemas.user import UserUpdate


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_profile(self, user: User) -> User:
        """Get user profile"""
        return user

    async def update_profile(self, user: User, update_data: UserUpdate) -> User:
        """Update user profile"""
        update_dict = update_data.model_dump(exclude_unset=True)

        for field, value in update_dict.items():
            setattr(user, field, value)

        await self.db.flush()
        await self.db.refresh(user)

        return user

    async def get_my_bookings(
        self,
        user: User,
        page: int = 1,
        page_size: int = 10
    ):
        """Get user's bookings with pagination"""
        offset = (page - 1) * page_size

        # Get total count
        count_result = await self.db.execute(
            select(Booking).where(Booking.user_id == user.id)
        )
        total = len(count_result.scalars().all())

        # Get paginated bookings with relationships
        result = await self.db.execute(
            select(Booking)
            .where(Booking.user_id == user.id)
            .options(
                selectinload(Booking.hotel),
                selectinload(Booking.room),
                selectinload(Booking.guests)
            )
            .order_by(Booking.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        bookings = result.scalars().all()

        return {
            "bookings": bookings,
            "total": total,
            "page": page,
            "page_size": page_size
        }
