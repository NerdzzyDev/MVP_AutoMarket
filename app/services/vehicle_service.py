from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.user import User
from app.models.vehicle import Vehicle


class VehicleService:
    @staticmethod
    async def get_user_vehicles(db: AsyncSession, user: User):
        result = await db.execute(select(Vehicle).where(Vehicle.user_id == user.id))
        return result.scalars().all()

    @staticmethod
    async def add_vehicle(db: AsyncSession, user: User, vehicle_data):
        vehicle = Vehicle(
            user_id=user.id,
            vin=vehicle_data.vin,
            brand=vehicle_data.brand,
            model=vehicle_data.model,
            engine=vehicle_data.engine,
            kba_code=vehicle_data.kba_code,
        )
        db.add(vehicle)
        await db.commit()
        await db.refresh(vehicle)
        return vehicle

    @staticmethod
    async def delete_vehicle(db: AsyncSession, user: User, vehicle_id: int):
        result = await db.execute(select(Vehicle).where(Vehicle.user_id == user.id, Vehicle.id == vehicle_id))
        vehicle = result.scalar_one_or_none()
        if not vehicle:
            raise HTTPException(status_code=404, detail="Vehicle not found")
        await db.delete(vehicle)
        await db.commit()
        return {"detail": "Vehicle deleted"}

    @staticmethod
    async def select_vehicle(db: AsyncSession, user: User, vehicle_id: int):
        # Получаем машину для выбора
        result = await db.execute(select(Vehicle).where(Vehicle.user_id == user.id, Vehicle.id == vehicle_id))
        vehicle_to_select = result.scalar_one_or_none()
        if not vehicle_to_select:
            raise HTTPException(status_code=404, detail="Vehicle not found")

        # Сбрасываем все остальные авто
        result = await db.execute(select(Vehicle).where(Vehicle.user_id == user.id))
        all_vehicles = result.scalars().all()
        for v in all_vehicles:
            v.is_selected = False

        vehicle_to_select.is_selected = True
        await db.commit()
        await db.refresh(vehicle_to_select)
        return vehicle_to_select
