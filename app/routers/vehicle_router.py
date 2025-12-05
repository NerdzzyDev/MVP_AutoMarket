# app/routers/vehicle_router.py
from fastapi import APIRouter, Depends, Form, HTTPException, Path, UploadFile, status
from loguru import logger
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_async_db as get_db
from app.models.user import User
from app.models.vehicle import Vehicle
from app.routers.user_router import get_current_user
from app.schemas.vehicle_schema import VehicleCreate, VehicleResponse
from app.services.vehicle_service import VehicleService


import aiohttp
from app.agents_tools.get_car_model import AutoteileMarktAgent
from app.schemas.kba import KBAVehicleInfo

router = APIRouter(prefix="/vehicles", tags=["vehicles"])


@router.get("/", response_model=list[VehicleResponse])
async def list_vehicles(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        vehicles = await VehicleService.get_user_vehicles(db, current_user)
        logger.info(f"User {current_user.email} listed {len(vehicles)} vehicles")
        return vehicles
    except SQLAlchemyError as e:
        logger.error(f"DB error while listing vehicles for {current_user.email}: {e}")
        raise HTTPException(status_code=500, detail="Database error while fetching vehicles")
    except Exception as e:
        logger.exception(f"Unexpected error in list_vehicles for {current_user.email}: {e}")
        raise HTTPException(status_code=500, detail="Unexpected error occurred")


@router.post("/", response_model=VehicleResponse)
async def add_vehicle(
    vehicle_data: VehicleCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    try:
        # создаём через сервис, теперь передаём search_code
        vehicle = await VehicleService.add_vehicle(db, current_user, vehicle_data)
        logger.info(f"User {current_user.email} added vehicle {vehicle.id}")
        return vehicle
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f"DB error while adding vehicle for {current_user.email}: {e}")
        raise HTTPException(status_code=500, detail="Database error while adding vehicle")
    except Exception as e:
        await db.rollback()
        logger.exception(f"Unexpected error in add_vehicle for {current_user.email}: {e}")
        raise HTTPException(status_code=500, detail="Unexpected error occurred")


@router.delete("/{vehicle_id}")
async def delete_vehicle(
    vehicle_id: int = Path(...), db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    try:
        result = await VehicleService.delete_vehicle(db, current_user, vehicle_id)
        logger.info(f"User {current_user.email} deleted vehicle {vehicle_id}")
        return result
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f"DB error while deleting vehicle {vehicle_id} for {current_user.email}: {e}")
        raise HTTPException(status_code=500, detail="Database error while deleting vehicle")
    except Exception as e:
        await db.rollback()
        logger.exception(f"Unexpected error in delete_vehicle for {current_user.email}: {e}")
        raise HTTPException(status_code=500, detail="Unexpected error occurred")


@router.patch("/{vehicle_id}/select", response_model=VehicleResponse)
async def select_vehicle(
    vehicle_id: int = Path(...), db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    try:
        vehicle = await VehicleService.select_vehicle(db, current_user, vehicle_id)
        logger.info(f"User {current_user.email} selected vehicle {vehicle_id}")
        return vehicle
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f"DB error while selecting vehicle {vehicle_id} for {current_user.email}: {e}")
        raise HTTPException(status_code=500, detail="Database error while selecting vehicle")
    except Exception as e:
        await db.rollback()
        logger.exception(f"Unexpected error in select_vehicle for {current_user.email}: {e}")
        raise HTTPException(status_code=500, detail="Unexpected error occurred")


@router.post("/add-from-doc", response_model=VehicleResponse)
async def add_vehicle_from_doc(
    vin: str | None = Form(None, description="VIN or KBA code of the vehicle"),
    search_code: str | None = Form(None, description="Optional vehicle search code extracted from document"),
    document: UploadFile | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Add a vehicle by either:
    - VIN/KBA code (`vin`)
    - Or uploading a STS document (`document`) to extract vehicle data
    Optional `search_code` can be provided to help searching parts.
    """

    if not vin and not document:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="You must provide either vin/kba or a document."
        )

    # Здесь можно добавить логику распознавания документа
    # Пока мок: если есть документ, просто создаем vehicle с test VIN
    try:
        vehicle = Vehicle(
            user_id=current_user.id,
            vin=vin or "MOCK_VIN_FROM_DOC",
            brand="MockBrand",
            model="MockModel",
            engine="MockEngine",
            kba_code=vin or "MOCK_KBA",
            search_code=search_code,
        )
        db.add(vehicle)
        await db.commit()
        await db.refresh(vehicle)
        logger.info(f"User {current_user.email} added vehicle {vehicle.id} via doc or VIN")
        return vehicle
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f"DB error while adding vehicle for {current_user.email}: {e}")
        raise HTTPException(status_code=500, detail="Database error while adding vehicle")
    except Exception as e:
        await db.rollback()
        logger.exception(f"Unexpected error while adding vehicle for {current_user.email}: {e}")
        raise HTTPException(status_code=500, detail="Unexpected error occurred")


@router.post("/by-kba", response_model=KBAVehicleInfo)
async def get_vehicle_by_kba(
    hsn: str = Form(
        ...,
        min_length=4,
        max_length=4,
        pattern=r"^\d{4}$",
        description="HSN (4 digits)",
    ),
    tsn: str = Form(
        ...,
        min_length=1,
        max_length=3,
        pattern=r"^[A-Za-z0-9]+$",
        description="TSN (1–3 symbols)",
    ),
):
    try:
        async with aiohttp.ClientSession() as session:
            agent = AutoteileMarktAgent(session)
            result = await agent.fetch_vehicle(hsn.strip(), tsn.upper().strip())

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vehicle not found by given HSN/TSN",
            )

        if not result.get("kba_id"):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="KBA ID not detected in response",
            )

        # Явно мапим в Pydantic-модель (чтобы не зависеть от лишних ключей в dict)
        return KBAVehicleInfo(
            brand=result.get("brand"),
            model=result.get("model"),
            engine=result.get("engine"),
            kba_id=result.get("kba_id"),
            url=result.get("url"),
            search_code=result.get("search_code"),
        )

    except aiohttp.ClientError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service autoteile-markt.de is unavailable",
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}",
        )
