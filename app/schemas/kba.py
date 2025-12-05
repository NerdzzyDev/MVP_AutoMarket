from pydantic import BaseModel, Field
from typing import Optional


class KBAForm(BaseModel):
    hsn: str = Field(..., min_length=4, max_length=4, pattern=r"^\d{4}$", description="HSN (4 digits)")
    tsn: str = Field(..., min_length=1, max_length=3, pattern=r"^[A-Za-z0-9]+$", description="TSN (1–3 symbols)")



class KBAVehicleInfo(BaseModel):
    brand: Optional[str] = None
    model: Optional[str] = None
    engine: Optional[str] = None
    kba_id: Optional[str] = None
    url: Optional[str] = None
    search_code: Optional[str] = None