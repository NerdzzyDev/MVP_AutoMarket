from pydantic import BaseModel


class CartItemResponse(BaseModel):
    id: int
    vin: str | None
    quantity: int
    product: dict

    class Config:
        orm_mode = True
