from pydantic import BaseModel


class VehicleBase(BaseModel):
    vin: str
    brand: str
    model: str
    engine: str
    kba_code: str
    search_code: str | None = None  # <- новое поле


class VehicleCreate(VehicleBase):
    pass


class VehicleResponse(VehicleBase):
    id: int
    is_selected: bool

    class Config:
        from_attributes = True
