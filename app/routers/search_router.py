from fastapi import APIRouter, File, HTTPException, Query, UploadFile, status
import json
from enum import Enum
from pydantic import BaseModel
from typing import List, Optional

from app.agents_tools.parser import AutoteileMarktParserAgent
from app.core.orchestrator import PartSearchOrchestrator
from app.schemas.search import SearchResponse, SearchResponseData, SearchParametersUsed, VehicleModel, PartPosition, Brand




# class PartPosition(str, Enum):
#     front = "front"
#     rear = "rear"


# class Brand(str, Enum):
#     RIDEX = "RIDEX"
#     Brembo = "Brembo"
#     ATE = "ATE"
#     Bosch = "Bosch"
#     Textar = "Textar"
#     Zimmermann = "Zimmermann"
#     Jurid = "Jurid"
#     Febi_Bilstein = "Febi Bilstein"
#     TRW = "TRW"
#     Meyle = "Meyle"


# class PartType(str, Enum):
#     BRAKE_PADS = "Bremsbelag"
#     BRAKE_DISCS = "Bremscheibe"
#     OIL_FILTER = "Ölfilter"
#     AIR_FILTER = "Luftfilter"
#     SPARK_PLUG = "Zündkerze"
#     TIRE = "Reifen"


# class VehicleModel(BaseModel):
#     brand_model: str
#     engine: str
#     kba_id: str
#     url: str


# class SearchParametersUsed(BaseModel):
#     vin_recognized: Optional[str] = None
#     kba_recognized: Optional[str] = None
#     identified_part_type: Optional[str] = None
#     vehicle_model: Optional[VehicleModel] = None


# class Product(BaseModel):
#     product_url: str
#     title: str
#     image_url: str
#     price: str
#     seller_name: str
#     delivery_time: str
#     description: str
#     brand: str
#     position: Optional[str] = None


# class SearchResponseData(BaseModel):
#     products: List[Product]
#     search_parameters_used: SearchParametersUsed


# class SearchResponse(BaseModel):
#     status: str
#     data: SearchResponseData


router = APIRouter(prefix="/search", tags=["search"])

# Создаем парсер
parser_agent = AutoteileMarktParserAgent()

# Пока фиксированные параметры
MOCK_SEARCH_PARAMETERS = SearchParametersUsed(
    vin_recognized="WVWZZZ3CZLE073029",
    kba_recognized="0603/BRA",
    identified_part_type="Bremsbelag",
    vehicle_model=VehicleModel(
        brand_model="VW Passat B8 Variant (3G)",
        engine="2.0 TDI",
        kba_id="19080",
        url="https://www.autoteile-markt.de/shop/q-lamp/vw-passat-b8-variant-(3g)-2.0-tdi-ersatzteile-fi19080"
    )
)

@router.post("/", response_model=SearchResponse)
async def search_parts(
    search_code: str | None = Query(None, description="! *search_code* from Vehicle table"),
    #document: UploadFile | None = File(None, description="Optional STS document photo."),
    query_text: str | None = Query(None, description="Free-text search for a part name."),
    #part_photo: UploadFile | None = File(None, description="Optional photo of a part."),
    position: PartPosition | None = Query(None, description="Filter by part position."),
    brand_filter: list[Brand] | None = Query(None, description="Filter by specific brands."),
    price_min: float | None = Query(None, description="Minimum price filter."),
    price_max: float | None = Query(None, description="Maximum price filter."),
    page: int = Query(1, ge=1, description="Page number for pagination."),
    limit: int = Query(10, ge=1, le=100, description="Number of results per page."),
):
    if not query_text:
        # raise HTTPException(
        #     status_code=400,
        #     detail="You must provide query_text",
        # )
        query_text = search_code # УБРАТЬ СТРОКУ, ВРЕМЕННАЯ ЗАГЛУШКА ДЛЯ ДИМЫ!!!!!!!!!!!


    orchestrator = PartSearchOrchestrator()
    # Передаем фильтры прямо в оркестратор
    return await orchestrator.search(
        search_code=search_code,
        query_text=query_text,
        position_flag=position,
        max_products=limit,
        min_price=price_min,
        max_price=price_max,
        brand_filter=brand_filter  # если добавим фильтр по бренду внутри orchestrator
    )
# @router.post("/", response_model=SearchResponse)
# async def search_parts(
#     search_code: str | None = Query(None, description="! *search_code* from Vehicle table"),
#     document: UploadFile | None = File(None, description="Optional STS document photo."),
#     query_text: str | None = Query(None, description="Free-text search for a part name."),
#     part_photo: UploadFile | None = File(None, description="Optional photo of a part."),
#     position: PartPosition | None = Query(None, description="Filter by part position."),
#     brand_filter: list[Brand] | None = Query(None, description="Filter by specific brands."),
#     price_min: float | None = Query(None, description="Minimum price filter."),
#     price_max: float | None = Query(None, description="Maximum price filter."),
#     page: int = Query(1, ge=1, description="Page number for pagination."),
#     limit: int = Query(10, ge=1, le=100, description="Number of results per page."),
# ):
#     if not search_code:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="You must provide search_code for now"
#         )

#     # 🔹 Поиск через реальный парсер
#     html_products = await parser_agent.search_parts_by_oem(search_code, max_products=limit)
#     data = json.loads(html_products)

#     products: List[Product] = []
#     for p in data.get("products", []):
#         products.append(Product(
#             product_url=p.get("product_url", ""),
#             title=p.get("title", ""),
#             image_url=p.get("image_url", ""),
#             price=p.get("price", ""),
#             seller_name=p.get("seller_name", ""),
#             delivery_time=p.get("delivery_time", ""),
#             description=p.get("description", ""),
#             brand=p.get("brand", ""),
#             position=p.get("position")
#         ))

#     return SearchResponse(
#         status="ok",
#         data=SearchResponseData(
#             products=products,
#             search_parameters_used=MOCK_SEARCH_PARAMETERS
#         )
#     )
