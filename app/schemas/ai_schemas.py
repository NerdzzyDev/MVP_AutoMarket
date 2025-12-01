from typing import Literal

from pydantic import BaseModel, Field
from typing import Optional

# ─────────────────────────────────────────────────────────────
# 📌 Base schemas
# ─────────────────────────────────────────────────────────────


class VehicleDataResponse(BaseModel):
    """Extracted vehicle info from OCR"""

    vin: str | None = Field(None, example="WBA3A5G51FNS12345")
    kba_hsn: str | None = Field(None, example="1234")
    kba_tsn: str | None = Field(None, example="567")


# ─────────────────────────────────────────────────────────────
# 📦 Marketplace search results
# ─────────────────────────────────────────────────────────────


class PartItem(BaseModel):
    """One product listing from marketplace"""

    part_name: str | None = Field(None, example="Brake Pad Set")
    photo_url: str | None = Field(None, example="https://example.com/image.jpg")
    price: str | None = Field(None, example="29.90 €")
    shop_name: str | None = Field(None, example="AutoTeile GmbH")
    product_url: str | None = Field(None, example="https://autoteile-markt.de/shop/item/123")
    delivery_time: str | None = Field(None, example="2-3 working days")


class PartSearchResult(BaseModel):
    """Detailed result of a part search"""

    vin: str = Field(..., example="WBA3A5G51FNS12345")
    kba_hsn: str = Field(..., example="1234")
    kba_tsn: str = Field(..., example="567")
    part_type: str = Field(..., example="Headlight")
    oem: list[str] 
    products: list[PartItem]


class FullResponse(BaseModel):
    """General wrapper with status + data"""

    status: Literal["ok", "error"]
    result: PartSearchResult | None = None
    error: str | None = None


# ─────────────────────────────────────────────────────────────
# 🔍 Search & query schemas
# ─────────────────────────────────────────────────────────────


class OEMRequest(BaseModel):
    """Used for marketplace search by OEM"""

    oem_number: str = Field(..., example="63117271901")
    max_products: int = Field(..., example=5, ge=1, le=50)


class QueryRequest(BaseModel):
    """LLM plain-text input"""

    input: str = Field(..., example="What part is this?")


class OEMSearchRequest(BaseModel):
    """Search OEM numbers by car data (at least 1 field required)"""
    vin: str | None = Field(None, example="SJNFAAZE0U6049190")
    hsn: str | None = Field(None, example="0005")
    tsn: str | None = Field(None, example="AFX")
    part_type: str | None = Field(None, example="Headlight")
    limit: int = Field(..., example=10, ge=1, le=100)

