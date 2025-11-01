# app/routers/vehicle_router.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_async_db as get_db
from app.models.user import User
from app.routers.user_router import get_current_user
from app.schemas.vehicle_schema import VehicleCreate, VehicleResponse
from app.services.vehicle_service import VehicleService

router = APIRouter(prefix="/vehicles", tags=["vehicles"])


@router.get("/", response_model=list[VehicleResponse])
async def list_vehicles(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    vehicles = await VehicleService.get_user_vehicles(db, current_user)
    return vehicles


@router.post("/", response_model=VehicleResponse)
async def add_vehicle(
    vehicle_data: VehicleCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    vehicle = await VehicleService.add_vehicle(db, current_user, vehicle_data)
    return vehicle


@router.delete("/{vehicle_id}")
async def delete_vehicle(
    vehicle_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    return await VehicleService.delete_vehicle(db, current_user, vehicle_id)


@router.patch("/{vehicle_id}/select", response_model=VehicleResponse)
async def select_vehicle(
    vehicle_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    vehicle = await VehicleService.select_vehicle(db, current_user, vehicle_id)
    return vehicle


@router.patch("/{vehicle_id}/select", response_model=VehicleResponse)
async def select_vehicle(
    vehicle_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    vehicle = await VehicleService.select_vehicle(db, current_user, vehicle_id)
    return vehicle
