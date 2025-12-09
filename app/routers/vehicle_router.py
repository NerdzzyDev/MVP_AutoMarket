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
from fastapi import APIRouter, File, Form, HTTPException, UploadFile, Query
from app.agents_tools.ocr import GoogleVisionOCRAgent, SparrowOCRAgent



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


@router.post("/identify/ocr-kba", response_model=KBAVehicleInfo, summary="Identify vehicle from document via OCR + KBA lookup")
async def identify_vehicle_from_ocr(
    file: UploadFile = File(..., description="Photo/scan of registration document"),
):
    """
    1) Принимает только изображение.
    2) Делает OCR (Google Vision → Sparrow fallback).
    3) Из текста вытаскивает VIN + HSN/TSN.
    4) По HSN/TSN ходит в AutoteileMarkt (как /by-kba).
    5) Возвращает KBAVehicleInfo (brand, model, engine, kba_id, url, search_code).

    Если:
      - OCR не смог вытащить HSN/TSN → 422
      - По KBA ничего не нашли → 404
      - В ответе нет kba_id → 422
    """

    # --- 1. Читаем картинку ---
    image_bytes = await file.read()
    logger.info(f"[OCR+KBA] Received file '{file.filename}' for vehicle identification")

    # --- 2. OCR: Google → Sparrow fallback (логика как в /identify/ocr) ---
    gv_agent = GoogleVisionOCRAgent()
    reserve_agent = SparrowOCRAgent()

    try:
        ocr_result = await gv_agent.extract_vehicle_data(image_bytes)
        if not ocr_result:
            raise Exception("Empty result from GoogleVisionOCRAgent")
        logger.info(f"[OCR][Google] Result: {ocr_result}")
    except Exception as err:
        logger.warning(f"[OCR][Google] Failed: {err}")
        ocr_result = await reserve_agent.extract_vehicle_data(image_bytes)
        logger.info(f"[OCR][Sparrow] Result: {ocr_result}")

    logger.debug(f"[OCR+KBA] Combined OCR result: {ocr_result}")

    vin = ocr_result.get("vin")
    kba = ocr_result.get("kba") or {}
    hsn = kba.get("hsn")
    tsn = kba.get("tsn")

    logger.info(f"[OCR+KBA] Parsed from OCR: vin={vin}, hsn={hsn}, tsn={tsn}")

    # --- 3. Проверяем, что HSN/TSN вообще нашлись ---
    if not hsn or not tsn:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Unable to detect HSN/TSN (KBA) from provided document",
        )

    # --- 4. Ходим в AutoteileMarkt по HSN/TSN (как в /by-kba) ---
    try:
        async with aiohttp.ClientSession() as session:
            agent = AutoteileMarktAgent(session)
            result = await agent.fetch_vehicle(hsn.strip(), tsn.upper().strip())

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vehicle not found by given HSN/TSN extracted from OCR",
            )

        if not result.get("kba_id"):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="KBA ID not detected in response from autoteile-markt.de",
            )

        logger.info(
            f"[OCR+KBA] Vehicle found for hsn={hsn}, tsn={tsn}: {result}"
        )

        # --- 5. Мапим в KBAVehicleInfo (так же, как в /by-kba) ---
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
    except HTTPException:
        # перекидываем дальше 404/422, которые сами кинули выше
        raise
    except Exception as e:
        logger.exception(f"[OCR+KBA] Unexpected error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}",
        )



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
