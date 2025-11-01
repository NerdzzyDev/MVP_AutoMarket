from pydantic import BaseModel


class FavoriteResponse(BaseModel):
    id: int
    vin: str | None
    product: dict

    class Config:
        orm_mode = True
