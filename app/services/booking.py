from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status
from typing import List, Optional
from datetime import date, timedelta

from app.models.booking import Booking, BookingStatus
from app.models.hotel import Hotel
from app.models.room import Room
from app.models.inventory import Inventory
from app.models.guest import Guest
from app.models.payment import Payment, PaymentStatus
from app.models.user import User, UserRole
from app.schemas.booking import BookingCreate, BookingAddGuests, BookingCancel


class BookingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def init_booking(self, user: User, booking_data: BookingCreate) -> Booking:
        """Initialize a new booking"""
        # Validate dates
        if booking_data.check_in_date >= booking_data.check_out_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Check-out date must be after check-in date"
            )

        if booking_data.check_in_date < date.today():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Check-in date cannot be in the past"
            )

        # Verify hotel exists and is active
        hotel_result = await self.db.execute(
            select(Hotel).where(Hotel.id == booking_data.hotel_id, Hotel.is_active == True)
        )
        hotel = hotel_result.scalar_one_or_none()
        if not hotel:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Hotel not found or not active"
            )

        # Verify room exists and belongs to hotel
        room_result = await self.db.execute(
            select(Room).where(
                Room.id == booking_data.room_id,
                Room.hotel_id == booking_data.hotel_id
            )
        )
        room = room_result.scalar_one_or_none()
        if not room:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Room not found in this hotel"
            )

        # Check availability for all dates
        nights = (booking_data.check_out_date - booking_data.check_in_date).days
        total_price = 0.0

        for i in range(nights):
            inv_date = booking_data.check_in_date + timedelta(days=i)
            inv_result = await self.db.execute(
                select(Inventory).where(
                    Inventory.room_id == room.id,
                    Inventory.date == inv_date
                )
            )
            inventory = inv_result.scalar_one_or_none()

            if not inventory:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"No inventory available for date {inv_date}"
                )

            available = inventory.available_count - inventory.booked_count
            if available < booking_data.rooms_count:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Not enough rooms available for date {inv_date}"
                )

            total_price += inventory.price * booking_data.rooms_count

        # Create booking
        booking = Booking(
            user_id=user.id,
            hotel_id=booking_data.hotel_id,
            room_id=booking_data.room_id,
            check_in_date=booking_data.check_in_date,
            check_out_date=booking_data.check_out_date,
            rooms_count=booking_data.rooms_count,
            total_price=total_price,
            status=BookingStatus.PENDING,
            special_requests=booking_data.special_requests,
        )

        self.db.add(booking)
        await self.db.flush()
        await self.db.refresh(booking)

        # Reserve inventory (update booked_count)
        await self._reserve_inventory(booking)

        return booking

    async def _reserve_inventory(self, booking: Booking):
        """Reserve inventory for a booking"""
        nights = (booking.check_out_date - booking.check_in_date).days

        for i in range(nights):
            inv_date = booking.check_in_date + timedelta(days=i)
            inv_result = await self.db.execute(
                select(Inventory).where(
                    Inventory.room_id == booking.room_id,
                    Inventory.date == inv_date
                )
            )
            inventory = inv_result.scalar_one_or_none()
            if inventory:
                inventory.booked_count += booking.rooms_count

        await self.db.flush()

    async def _release_inventory(self, booking: Booking):
        """Release inventory when booking is cancelled"""
        nights = (booking.check_out_date - booking.check_in_date).days

        for i in range(nights):
            inv_date = booking.check_in_date + timedelta(days=i)
            inv_result = await self.db.execute(
                select(Inventory).where(
                    Inventory.room_id == booking.room_id,
                    Inventory.date == inv_date
                )
            )
            inventory = inv_result.scalar_one_or_none()
            if inventory:
                inventory.booked_count = max(0, inventory.booked_count - booking.rooms_count)

        await self.db.flush()

    async def get_booking_by_id(self, booking_id: int, user: User) -> Booking:
        """Get booking by ID with ownership check"""
        result = await self.db.execute(
            select(Booking)
            .where(Booking.id == booking_id)
            .options(
                selectinload(Booking.hotel),
                selectinload(Booking.room),
                selectinload(Booking.guests),
                selectinload(Booking.payment)
            )
        )
        booking = result.scalar_one_or_none()

        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Booking not found"
            )

        # Check ownership (user owns booking or is hotel admin/admin)
        if booking.user_id != user.id:
            # Check if user is hotel admin
            hotel_result = await self.db.execute(
                select(Hotel).where(Hotel.id == booking.hotel_id)
            )
            hotel = hotel_result.scalar_one_or_none()

            if user.role != UserRole.ADMIN and (not hotel or hotel.owner_id != user.id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to access this booking"
                )

        return booking

    async def add_guests_to_booking(
        self,
        booking_id: int,
        user: User,
        guest_data: BookingAddGuests
    ) -> Booking:
        """Add guests to a booking"""
        booking = await self.get_booking_by_id(booking_id, user)

        if booking.status not in [BookingStatus.PENDING, BookingStatus.CONFIRMED]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot add guests to this booking"
            )

        # Get guests
        guest_result = await self.db.execute(
            select(Guest).where(
                Guest.id.in_(guest_data.guest_ids),
                Guest.user_id == user.id
            )
        )
        guests = guest_result.scalars().all()

        if len(guests) != len(guest_data.guest_ids):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Some guests not found"
            )

        # Add guests to booking
        booking.guests.extend(guests)
        await self.db.flush()
        await self.db.refresh(booking)

        return booking

    async def get_booking_status(self, booking_id: int, user: User):
        """Get booking status"""
        booking = await self.get_booking_by_id(booking_id, user)

        payment_status = None
        if booking.payment:
            payment_status = booking.payment.status.value

        return {
            "booking_id": booking.id,
            "status": booking.status,
            "payment_status": payment_status
        }

    async def cancel_booking(
        self,
        booking_id: int,
        user: User,
        cancel_data: BookingCancel
    ) -> Booking:
        """Cancel a booking"""
        booking = await self.get_booking_by_id(booking_id, user)

        if booking.status in [BookingStatus.CANCELLED, BookingStatus.CHECKED_OUT]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Booking cannot be cancelled"
            )

        # Release inventory
        await self._release_inventory(booking)

        # Update booking status
        booking.status = BookingStatus.CANCELLED
        booking.cancellation_reason = cancel_data.reason

        # If payment exists and was completed, mark for refund
        if booking.payment and booking.payment.status == PaymentStatus.COMPLETED:
            booking.payment.status = PaymentStatus.REFUNDED

        await self.db.flush()
        await self.db.refresh(booking)

        return booking

    async def get_hotel_bookings(
        self,
        hotel_id: int,
        user: User,
        page: int = 1,
        page_size: int = 10,
        status_filter: Optional[BookingStatus] = None
    ):
        """Get all bookings for a hotel (admin)"""
        # Verify hotel access
        hotel_result = await self.db.execute(
            select(Hotel).where(Hotel.id == hotel_id)
        )
        hotel = hotel_result.scalar_one_or_none()

        if not hotel:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Hotel not found"
            )

        if user.role != UserRole.ADMIN and hotel.owner_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this hotel's bookings"
            )

        offset = (page - 1) * page_size

        # Build query
        query = select(Booking).where(Booking.hotel_id == hotel_id)
        count_query = select(func.count(Booking.id)).where(Booking.hotel_id == hotel_id)

        if status_filter:
            query = query.where(Booking.status == status_filter)
            count_query = count_query.where(Booking.status == status_filter)

        # Get total count
        count_result = await self.db.execute(count_query)
        total = count_result.scalar()

        # Get paginated bookings
        result = await self.db.execute(
            query.options(
                selectinload(Booking.user),
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

    async def get_hotel_report(
        self,
        hotel_id: int,
        user: User,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ):
        """Generate booking report for a hotel"""
        # Verify hotel access
        hotel_result = await self.db.execute(
            select(Hotel).where(Hotel.id == hotel_id)
        )
        hotel = hotel_result.scalar_one_or_none()

        if not hotel:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Hotel not found"
            )

        if user.role != UserRole.ADMIN and hotel.owner_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this hotel's reports"
            )

        # Default date range: last 30 days
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=30)

        # Get all bookings in date range
        result = await self.db.execute(
            select(Booking).where(
                Booking.hotel_id == hotel_id,
                Booking.created_at >= start_date,
                Booking.created_at <= end_date + timedelta(days=1)
            )
        )
        bookings = result.scalars().all()

        # Calculate statistics
        total_bookings = len(bookings)
        confirmed_bookings = len([b for b in bookings if b.status == BookingStatus.CONFIRMED])
        cancelled_bookings = len([b for b in bookings if b.status == BookingStatus.CANCELLED])
        pending_bookings = len([b for b in bookings if b.status == BookingStatus.PENDING])

        total_revenue = sum(
            b.total_price for b in bookings
            if b.status in [BookingStatus.CONFIRMED, BookingStatus.CHECKED_IN, BookingStatus.CHECKED_OUT]
        )

        average_booking_value = total_revenue / confirmed_bookings if confirmed_bookings > 0 else 0

        # Calculate occupancy rate (simplified)
        # Get total room capacity for the hotel
        room_result = await self.db.execute(
            select(func.sum(Room.total_count)).where(Room.hotel_id == hotel_id)
        )
        total_rooms = room_result.scalar() or 0

        days_in_period = (end_date - start_date).days + 1
        total_room_nights = total_rooms * days_in_period

        booked_room_nights = sum(
            b.rooms_count * (b.check_out_date - b.check_in_date).days
            for b in bookings
            if b.status in [BookingStatus.CONFIRMED, BookingStatus.CHECKED_IN, BookingStatus.CHECKED_OUT]
        )

        occupancy_rate = (booked_room_nights / total_room_nights * 100) if total_room_nights > 0 else 0

        return {
            "hotel_id": hotel_id,
            "hotel_name": hotel.name,
            "total_bookings": total_bookings,
            "confirmed_bookings": confirmed_bookings,
            "cancelled_bookings": cancelled_bookings,
            "pending_bookings": pending_bookings,
            "total_revenue": total_revenue,
            "average_booking_value": average_booking_value,
            "occupancy_rate": round(occupancy_rate, 2),
            "report_period_start": start_date,
            "report_period_end": end_date
        }
