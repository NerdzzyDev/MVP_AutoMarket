# app/schemas/search.py
from pydantic import BaseModel
from typing import List, Optional
from enum import Enum


class PartPosition(str, Enum):
    front = "front"
    rear = "rear"


class Brand(str, Enum):
    RIDEX = "RIDEX"
    Brembo = "Brembo"
    ATE = "ATE"
    Bosch = "Bosch"
    Textar = "Textar"
    Zimmermann = "Zimmermann"
    Jurid = "Jurid"
    Febi_Bilstein = "Febi Bilstein"
    TRW = "TRW"
    Meyle = "Meyle"


class PartType(str, Enum):
    BRAKE_PADS = "Bremsbelag"
    BRAKE_DISCS = "Bremscheibe"
    OIL_FILTER = "Ölfilter"
    AIR_FILTER = "Luftfilter"
    SPARK_PLUG = "Zündkerze"
    TIRE = "Reifen"


class VehicleModel(BaseModel):
    brand_model: str
    engine: str
    kba_id: str
    url: str


class SearchParametersUsed(BaseModel):
    vin_recognized: Optional[str] = None
    kba_recognized: Optional[str] = None
    identified_part_type: Optional[str] = None
    vehicle_model: Optional[VehicleModel] = None


class Product(BaseModel):
    product_url: str
    title: str
    image_url: str
    price: str
    seller_name: str
    delivery_time: str
    description: str
    brand: str
    position: Optional[str] = None


class SearchResponseData(BaseModel):
    products: List[Product]
    search_parameters_used: SearchParametersUsed


class SearchResponse(BaseModel):
    status: str
    data: SearchResponseData