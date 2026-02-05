from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.db.session import get_db
from app.models.user import User
from app.schemas.guest import GuestCreate, GuestUpdate, GuestResponse, GuestListResponse
from app.services.guest import GuestService
from app.core.dependencies import get_current_active_user

router = APIRouter()


@router.post("", response_model=GuestResponse, status_code=status.HTTP_201_CREATED)
async def add_guest(
    guest_data: GuestCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Add a new guest to user's guest list"""
    guest_service = GuestService(db)
    return await guest_service.create_guest(current_user, guest_data)


@router.get("", response_model=GuestListResponse)
async def get_my_guests(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all guests for the current user"""
    guest_service = GuestService(db)
    guests = await guest_service.get_guests(current_user)
    return GuestListResponse(guests=guests, total=len(guests))


@router.get("/{guest_id}", response_model=GuestResponse)
async def get_guest(
    guest_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific guest by ID"""
    guest_service = GuestService(db)
    return await guest_service.get_guest_by_id(current_user, guest_id)


@router.put("/{guest_id}", response_model=GuestResponse)
async def update_guest(
    guest_id: int,
    update_data: GuestUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a guest"""
    guest_service = GuestService(db)
    return await guest_service.update_guest(current_user, guest_id, update_data)


@router.delete("/{guest_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_guest(
    guest_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Remove a guest"""
    guest_service = GuestService(db)
    await guest_service.delete_guest(current_user, guest_id)
    return None
