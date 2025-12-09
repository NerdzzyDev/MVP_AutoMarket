# app/schemas/search.py
from pydantic import BaseModel
from typing import List, Optional
from enum import Enum


class PartPosition(str, Enum):
    front = "front"
    rear = "rear"



class Brand(str, Enum):
    RIDEX = "RIDEX"              # ridex
    Brembo = "Brembo"           # brembo
    ATE = "ATE"                 # ate
    Bosch = "Bosch"             # bosch
    Textar = "Textar"           # textar
    Zimmermann = "Zimmermann"   # zimmermann
    Jurid = "Jurid"             # jurid
    Febi_Bilstein = "Febi Bilstein"  # febi-bilstein
    TRW = "TRW"                 # trw
    Meyle = "Meyle"             # meyle



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
    total_products: Optional[int] = 0


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