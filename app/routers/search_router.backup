from enum import Enum
from fastapi import APIRouter, File, HTTPException, Query, UploadFile, status
from pydantic import BaseModel
from typing import List, Optional
import random

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


# Реальные фото из твоего эталонного ответа
REAL_PRODUCT_PHOTOS = [
    "https://cdn.autoteile-markt.de/tecdoc/0358/13046027642N-SET-MS_550_500_75.webp",
    "https://cdn.autoteile-markt.de/tecdoc/0161/0161gdb3206_550_500_75.webp", 
    "https://cdn.autoteile-markt.de/tecdoc/0161/0161gdb3273_550_500_75.webp"
]

# Реальные описания из твоего эталонного ответа
REAL_DESCRIPTIONS = [
    "Das Produkt Bremsbelagsatz, Scheibenbremse des Herstellers MASTER-SPORT GERMANY hat die Breite 175 mm. Die Dicke/Stärke ist 20,1 mm, das Bruttogewicht beträgt 2,75 kg und die Höhe lautet 70 mm. Bremsbelagsatz, Scheibenbremse hat die ergänzenden Artikelinformationen mit Anti-Quietsch-Blech und passt beispielsweise zu Fahrzeugen von SKODA, VW und SEAT.Der angebotene Artikel wird unter anderem unter den Original Ersatzteilnummernbzw. Vergleichsnummern 3C0 698 151 E, 3C0 698 151 F, 7N0 698 151 A, 7N0 698 151 C, 7N0 698 151 D geführt.",
    "Das Produkt Bremsbelagsatz, Scheibenbremse des Herstellers TRW hat die Breite 91,6 mm. Der Artikel besitzt das Prüfzeichen E2 90R 01124/002, die Höhe lautet 64 mm und die Herstellereinschränkungen lauten SUMITOMO. Bremsbelagsatz, Scheibenbremse hat eine Dicke/Stärke von 15,5 mm und passt beispielsweise zu Fahrzeugen von KIA und MAZDA.Der angebotene Artikel wird unter anderem unter den Original Ersatzteilnummernbzw. Vergleichsnummern DCY0-33-23Z A, DCY0-33-23Z B, DCY03323Z, 0K30A3328Z, K0BA23328Z geführt.",
    "Das Produkt Bremsbelagsatz, Scheibenbremse des Herstellers TRW hat das Prüfzeichen E2 90R 01124/012. Die Herstellereinschränkungen lauten AKEBONO, die Breite beträgt 139,3 mm und die Höhe lautet 59,5 mm. Bremsbelagsatz, Scheibenbremse hat eine Dicke/Stärke von 14,8 mm und passt beispielsweise zu Fahrzeugen von INFINITI und NISSAN.Der angebotene Artikel wird unter anderem unter den Original Ersatzteilnummernbzw. Vergleichsnummern 41060-0P690, 41060-0P691, 41060-0P693, 41060-3Y690, 41060-60U90 geführt."
]

# Генератор товаров с реальными фото
class ProductGenerator:
    def __init__(self):
        self.brands = [brand.value for brand in Brand]
        self.part_types = {
            PartType.BRAKE_PADS: {
                "names": ["Bremsbelagsatz", "Bremsbeläge", "Bremsbelag-Set"],
                "positions": ["Vorderachse", "Hinterachse", "Vorderachse links", "Vorderachse rechts", "Hinterachse links", "Hinterachse rechts"]
            },
            PartType.BRAKE_DISCS: {
                "names": ["Bremsscheibe", "Bremsscheiben", "Bremsscheiben-Set"],
                "positions": ["Vorderachse", "Hinterachse", "Vorderachse links", "Vorderachse rechts", "Hinterachse links", "Hinterachse rechts"]
            },
            PartType.OIL_FILTER: {
                "names": ["Ölfilter", "Ölfiltereinsatz", "Ölfilterpatrone"],
                "positions": []
            },
            PartType.AIR_FILTER: {
                "names": ["Luftfilter", "Innenraumfilter", "Sportluftfilter"],
                "positions": []
            },
            PartType.SPARK_PLUG: {
                "names": ["Zündkerze", "Iridium-Zündkerze", "Doppelex-Zündkerze"],
                "positions": []
            },
            PartType.TIRE: {
                "names": ["Sommerreifen", "Winterreifen", "Ganzjahresreifen", "Sportreifen"],
                "positions": ["Vorderachse", "Hinterachse", "Komplettsatz 4 Stück"]
            }
        }
        
        self.delivery_times = [
            "1 - 3 Werktage", "2 - 5 Werktage", "3 - 7 Werktage", 
            "Sofort lieferbar", "1 - 2 Werktage", "5 - 10 Werktage"
        ]
        
        self.sellers = ["AutoTeile24", "Kfz-Teile Shop", "Ersatzteil Express", "Profı Auto", "Meister Werkstatt"]
    
    def generate_product(self, product_id: int, part_type: PartType = PartType.BRAKE_PADS):
        brand = random.choice(self.brands)
        
        # Если тип не найден, используем BRAKE_PADS как fallback
        if part_type not in self.part_types:
            part_type = PartType.BRAKE_PADS
            
        part_info = self.part_types[part_type]
        part_name = random.choice(part_info["names"])
        
        # Позиция - случайная из доступных или None
        position = random.choice(part_info["positions"]) if part_info["positions"] and random.random() > 0.3 else ""
        
        title = f"{part_name} {brand}"
        if position:
            title += f" {position}"
            
        # Разные ценовые диапазоны для разных типов товаров
        if part_type == PartType.TIRE:
            price = f"{random.randint(50, 200)},{random.randint(10, 99):02d} €"
        elif part_type in [PartType.BRAKE_PADS, PartType.BRAKE_DISCS]:
            price = f"{random.randint(30, 150)},{random.randint(10, 99):02d} €"
        else:
            price = f"{random.randint(10, 80)},{random.randint(10, 99):02d} €"
        
        # Случайное фото из реальных
        image_url = random.choice(REAL_PRODUCT_PHOTOS)
        # Случайное описание из реальных
        description = random.choice(REAL_DESCRIPTIONS)
        
        return Product(
            product_url=f"https://www.autoteile-markt.de/shop/artikel/{part_name.lower().replace(' ', '-')}-{brand.lower()}-{product_id}",
            title=title,
            image_url=image_url,
            price=price,
            seller_name=random.choice(self.sellers),
            delivery_time=random.choice(self.delivery_times),
            description=description,
            brand=brand,
            position=position if position else None
        )


# Создаем генератор
product_generator = ProductGenerator()

# Генерируем 50 тестовых товаров разных типов
MOCK_PRODUCTS = []
part_types = list(PartType)

for i in range(50):
    part_type = random.choice(part_types)
    MOCK_PRODUCTS.append(product_generator.generate_product(i + 1, part_type))

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
    document: UploadFile | None = File(None, description="Optional STS document photo."),
    query_text: str | None = Query(None, description="Free-text search for a part name."),
    part_photo: UploadFile | None = File(None, description="Optional photo of a part."),
    position: PartPosition | None = Query(None, description="Filter by part position."),
    brand_filter: list[Brand] | None = Query(None, description="Filter by specific brands."),
    price_min: float | None = Query(None, description="Minimum price filter."),
    price_max: float | None = Query(None, description="Maximum price filter."),
    page: int = Query(1, ge=1, description="Page number for pagination."),
    limit: int = Query(10, ge=1, le=100, description="Number of results per page."),
):
    if not any([search_code, document, query_text, part_photo]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must provide at least one of: search_code, document, query_text, or part_photo",
        )

    # Начинаем с полного списка продуктов
    filtered_products = MOCK_PRODUCTS.copy()
    
    # Фильтрация по тексту запроса
    if query_text:
        query_lower = query_text.lower()
        filtered_products = [
            p for p in filtered_products 
            if query_lower in p.title.lower() or query_lower in p.brand.lower()
        ]
    
    # Фильтрация по бренду
    if brand_filter:
        brand_values = [brand.value for brand in brand_filter]
        filtered_products = [p for p in filtered_products if p.brand in brand_values]
    
    # Фильтрация по позиции
    if position:
        position_german = "Vorderachse" if position == PartPosition.front else "Hinterachse"
        filtered_products = [p for p in filtered_products if p.position and position_german in p.position]
    
    # Фильтрация по цене (простая реализация)
    if price_min is not None:
        filtered_products = [
            p for p in filtered_products 
            if float(p.price.split(' ')[0].replace(',', '.')) >= price_min
        ]
    
    if price_max is not None:
        filtered_products = [
            p for p in filtered_products 
            if float(p.price.split(' ')[0].replace(',', '.')) <= price_max
        ]

    # Пагинация
    total = len(filtered_products)
    start = (page - 1) * limit
    end = start + limit
    paginated_products = filtered_products[start:end]

    return SearchResponse(
        status="ok",
        data=SearchResponseData(
            products=paginated_products,
            search_parameters_used=MOCK_SEARCH_PARAMETERS
        )
    )
