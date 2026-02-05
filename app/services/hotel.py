from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status
from typing import Optional, List
from datetime import date

from app.models.hotel import Hotel
from app.models.room import Room
from app.models.inventory import Inventory
from app.models.user import User, UserRole
from app.schemas.hotel import HotelCreate, HotelUpdate


class HotelService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_hotel(self, user: User, hotel_data: HotelCreate) -> Hotel:
        """Create a new hotel"""
        hotel = Hotel(
            owner_id=user.id,
            name=hotel_data.name,
            description=hotel_data.description,
            city=hotel_data.city,
            address=hotel_data.address,
            latitude=hotel_data.latitude,
            longitude=hotel_data.longitude,
            amenities=hotel_data.amenities,
            photos=hotel_data.photos,
            contact_email=hotel_data.contact_email,
            contact_phone=hotel_data.contact_phone,
            is_active=False,  # Needs activation
        )

        self.db.add(hotel)
        await self.db.flush()
        await self.db.refresh(hotel)

        return hotel

    async def get_hotel_by_id(self, hotel_id: int, user: Optional[User] = None) -> Hotel:
        """Get hotel by ID with optional ownership check"""
        result = await self.db.execute(
            select(Hotel).where(Hotel.id == hotel_id)
        )
        hotel = result.scalar_one_or_none()

        if not hotel:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Hotel not found"
            )

        # If user provided, check ownership (unless admin)
        if user and user.role != UserRole.ADMIN and hotel.owner_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this hotel"
            )

        return hotel

    async def get_admin_hotels(self, user: User, page: int = 1, page_size: int = 10):
        """Get hotels owned by the user (or all if admin)"""
        offset = (page - 1) * page_size

        query = select(Hotel)
        if user.role != UserRole.ADMIN:
            query = query.where(Hotel.owner_id == user.id)

        # Get total count
        count_query = select(func.count(Hotel.id))
        if user.role != UserRole.ADMIN:
            count_query = count_query.where(Hotel.owner_id == user.id)
        count_result = await self.db.execute(count_query)
        total = count_result.scalar()

        # Get paginated hotels
        result = await self.db.execute(
            query.order_by(Hotel.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        hotels = result.scalars().all()

        return {
            "hotels": hotels,
            "total": total,
            "page": page,
            "page_size": page_size
        }

    async def update_hotel(
        self,
        hotel_id: int,
        user: User,
        update_data: HotelUpdate
    ) -> Hotel:
        """Update hotel details"""
        hotel = await self.get_hotel_by_id(hotel_id, user)

        update_dict = update_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(hotel, field, value)

        await self.db.flush()
        await self.db.refresh(hotel)

        return hotel

    async def delete_hotel(self, hotel_id: int, user: User) -> None:
        """Delete a hotel"""
        hotel = await self.get_hotel_by_id(hotel_id, user)
        await self.db.delete(hotel)
        await self.db.flush()

    async def activate_hotel(self, hotel_id: int, user: User) -> Hotel:
        """Activate a hotel (make it visible for booking)"""
        hotel = await self.get_hotel_by_id(hotel_id, user)
        hotel.is_active = True
        await self.db.flush()
        await self.db.refresh(hotel)
        return hotel

    async def deactivate_hotel(self, hotel_id: int, user: User) -> Hotel:
        """Deactivate a hotel"""
        hotel = await self.get_hotel_by_id(hotel_id, user)
        hotel.is_active = False
        await self.db.flush()
        await self.db.refresh(hotel)
        return hotel

    # Public methods for hotel browsing
    async def search_hotels(
        self,
        city: Optional[str] = None,
        check_in_date: Optional[date] = None,
        check_out_date: Optional[date] = None,
        guests: Optional[int] = None,
        rooms: Optional[int] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        amenities: Optional[List[str]] = None,
        page: int = 1,
        page_size: int = 10
    ):
        """Search for available hotels"""
        offset = (page - 1) * page_size

        # Base query for active hotels
        query = select(Hotel).where(Hotel.is_active == True)
        count_query = select(func.count(Hotel.id)).where(Hotel.is_active == True)

        # Filter by city
        if city:
            query = query.where(Hotel.city.ilike(f"%{city}%"))
            count_query = count_query.where(Hotel.city.ilike(f"%{city}%"))

        # Get total count
        count_result = await self.db.execute(count_query)
        total = count_result.scalar()

        # Get paginated hotels
        result = await self.db.execute(
            query.options(selectinload(Hotel.rooms))
            .order_by(Hotel.rating.desc())
            .offset(offset)
            .limit(page_size)
        )
        hotels = result.scalars().all()

        # If date range provided, filter by availability
        if check_in_date and check_out_date and hotels:
            available_hotels = []
            for hotel in hotels:
                has_availability = await self._check_hotel_availability(
                    hotel, check_in_date, check_out_date, guests, rooms, min_price, max_price
                )
                if has_availability:
                    available_hotels.append(hotel)
            hotels = available_hotels
            total = len(hotels)

        return {
            "hotels": hotels,
            "total": total,
            "page": page,
            "page_size": page_size
        }

    async def _check_hotel_availability(
        self,
        hotel: Hotel,
        check_in_date: date,
        check_out_date: date,
        guests: Optional[int] = None,
        rooms: Optional[int] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None
    ) -> bool:
        """Check if hotel has available rooms for the date range"""
        for room in hotel.rooms:
            # Check capacity
            if guests and room.capacity < guests:
                continue

            # Check price range
            if min_price and room.base_price < min_price:
                continue
            if max_price and room.base_price > max_price:
                continue

            # Check inventory for all dates
            result = await self.db.execute(
                select(Inventory)
                .where(
                    Inventory.room_id == room.id,
                    Inventory.date >= check_in_date,
                    Inventory.date < check_out_date
                )
            )
            inventories = result.scalars().all()

            # Check if all dates have availability
            required_rooms = rooms or 1
            dates_needed = (check_out_date - check_in_date).days

            if len(inventories) >= dates_needed:
                all_available = all(
                    (inv.available_count - inv.booked_count) >= required_rooms
                    for inv in inventories
                )
                if all_available:
                    return True

        return False

    async def get_hotel_info(self, hotel_id: int) -> Hotel:
        """Get hotel details with rooms for public view"""
        result = await self.db.execute(
            select(Hotel)
            .where(Hotel.id == hotel_id, Hotel.is_active == True)
            .options(selectinload(Hotel.rooms))
        )
        hotel = result.scalar_one_or_none()

        if not hotel:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Hotel not found or not active"
            )

        return hotel
