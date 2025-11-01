from enum import Enum

from fastapi import APIRouter, File, HTTPException, Query, UploadFile, status
from pydantic import BaseModel

router = APIRouter(prefix="/search", tags=["search"])


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


class Product(BaseModel):
    id: int
    name: str
    brand: Brand
    price: float
    position: PartPosition | None = None
    description: str | None = None


class SearchResponse(BaseModel):
    results: list[Product]
    total: int


MOCK_PRODUCTS = [
    Product(id=1, name="Front brake pads set", brand=Brand.RIDEX, price=49.99, position=PartPosition.front),
    Product(id=2, name="Rear brake discs", brand=Brand.Brembo, price=89.99, position=PartPosition.rear),
    Product(id=3, name="Oil filter", brand=Brand.Bosch, price=15.5),
]


@router.post("/", response_model=SearchResponse)
async def search_parts(
    search_code: str | None = Query(None, description="! *search_code* from Vehicle table"),
    document: UploadFile | None = File(None, description="Optional STS document photo."),
    query_text: str | None = Query(None, description="Free-text search for a part name."),
    part_photo: UploadFile | None = File(None, description="Optional photo of a part."),
    position: PartPosition | None = Query(None, description="Filter by part position."),
    brand_filter: list[Brand] | None = Query(None, description="Filter by specific brands."),
    price_min: float | None = Query(None, description="Minimum price filter."),
    price_max: float | None = Query(None, description="Maximum price filter."),
    page: int = Query(1, ge=1, description="Page number for pagination."),
    limit: int = Query(10, ge=1, le=10, description="Number of results per page."),
):
    if not any([search_code, document, query_text, part_photo]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must provide at least one of: search_code, document, query_text, or part_photo",
        )

    results = MOCK_PRODUCTS.copy()

    if query_text:
        results = [p for p in results if query_text.lower() in p.name.lower()]
    if position:
        results = [p for p in results if p.position == position]
    if brand_filter:
        results = [p for p in results if p.brand in brand_filter]
    if price_min is not None:
        results = [p for p in results if p.price >= price_min]
    if price_max is not None:
        results = [p for p in results if p.price <= price_max]

    start = (page - 1) * limit
    end = start + limit
    paginated = results[start:end]

    return SearchResponse(results=paginated, total=len(results))
