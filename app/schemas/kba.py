from pydantic import BaseModel, Field

class KBAForm(BaseModel):
    hsn: str = Field(..., min_length=4, max_length=4, regex=r"^\d{4}$", description="HSN (4 digits)")
    tsn: str = Field(..., min_length=1, max_length=3, regex=r"^[A-Za-z0-9]+$", description="TSN (1–3 symbols)")


class KBAVehicleInfo(BaseModel):
    brand: str | None = None
    model: str | None = None
    engine: str | None = None
    kba_id: str | None = None
    url: str | None = None
