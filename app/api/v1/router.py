from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    users,
    guests,
    hotels,
    rooms,
    inventory,
    bookings,
    webhooks,
)

api_router = APIRouter()

# Authentication routes
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])

# User routes
api_router.include_router(users.router, prefix="/users", tags=["User Profile"])

# Guest routes
api_router.include_router(guests.router, prefix="/users/guests", tags=["Guests"])

# Hotel browse routes (public)
api_router.include_router(hotels.public_router, prefix="/hotels", tags=["Hotel Browse"])

# Hotel admin routes
api_router.include_router(hotels.admin_router, prefix="/admin/hotels", tags=["Hotel Management"])

# Room admin routes
api_router.include_router(rooms.router, prefix="/admin/hotels", tags=["Room Management"])

# Inventory admin routes
api_router.include_router(inventory.router, prefix="/admin/inventory", tags=["Inventory Management"])

# Booking routes
api_router.include_router(bookings.router, prefix="/bookings", tags=["Booking Flow"])

# Admin booking routes
api_router.include_router(bookings.admin_router, prefix="/admin/hotels", tags=["Admin Bookings"])

# Webhook routes
api_router.include_router(webhooks.router, prefix="/webhook", tags=["Webhooks"])
