from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import date

from app.db.session import get_db
from app.models.user import User
from app.schemas.inventory import (
    InventoryUpdate,
    InventoryBulkUpdate,
    InventoryResponse,
    InventoryListResponse,
)
from app.services.inventory import InventoryService
from app.core.dependencies import get_current_hotel_admin

router = APIRouter()


@router.get("/rooms/{room_id}", response_model=InventoryListResponse)
async def get_room_inventory(
    room_id: int,
    start_date: Optional[date] = Query(None, description="Start date for inventory"),
    end_date: Optional[date] = Query(None, description="End date for inventory"),
    current_user: User = Depends(get_current_hotel_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get inventory for a room within a date range"""
    inventory_service = InventoryService(db)
    inventories = await inventory_service.get_room_inventory(
        room_id, current_user, start_date, end_date
    )
    return InventoryListResponse(
        inventories=inventories,
        room_id=room_id,
        total=len(inventories)
    )


@router.patch("/rooms/{room_id}", response_model=InventoryListResponse)
async def update_room_inventory(
    room_id: int,
    bulk_data: InventoryBulkUpdate,
    current_user: User = Depends(get_current_hotel_admin),
    db: AsyncSession = Depends(get_db)
):
    """Update inventory for a room within a date range"""
    inventory_service = InventoryService(db)
    inventories = await inventory_service.bulk_update_inventory(
        room_id, current_user, bulk_data
    )
    return InventoryListResponse(
        inventories=inventories,
        room_id=room_id,
        total=len(inventories)
    )


@router.patch("/rooms/{room_id}/date/{inv_date}", response_model=InventoryResponse)
async def update_inventory_for_date(
    room_id: int,
    inv_date: date,
    update_data: InventoryUpdate,
    current_user: User = Depends(get_current_hotel_admin),
    db: AsyncSession = Depends(get_db)
):
    """Update inventory for a specific date"""
    inventory_service = InventoryService(db)
    return await inventory_service.update_inventory(
        room_id, inv_date, current_user, update_data
    )
