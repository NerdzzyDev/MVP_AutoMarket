from typing import Optional
from app.agents_tools.parser import AutoteileMarktParserAgent
from app.agents_tools.part_text import TextPartIdentifierAgent
from loguru import logger

import json
from typing import Optional
from app.schemas.search import SearchResponse, SearchResponseData, SearchParametersUsed, VehicleModel, PartPosition
import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class PartSearchOrchestrator:
    def __init__(self):
        self.text_agent = TextPartIdentifierAgent()
        self.parser_agent = AutoteileMarktParserAgent()
        self.mock_search_code = "vw-passat-b8-variant-(3g)-2.0-tdi-ersatzteile-fi19080"

    async def search(
        self,
        query_text: str,
        position_flag: Optional[str] = None,
        max_products: int = 10,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
    ) -> SearchResponse:
        # Шаг 1: нормализация запроса
        normalized_query = await self.text_agent.normalize_query(query_text, position_flag)

        # Шаг 2: поиск через парсер
        search_result_json = await self.parser_agent.search_parts_by_oem(
            oem_number=normalized_query,
            max_products=max_products,
            model_link=self.mock_search_code
        )
        search_result = json.loads(search_result_json or "{}")

        # Шаг 3: формируем список продуктов с безопасными полями
        products = []
        for p in search_result.get("products", []):
            try:
                price_val = float(p.get("price", "0").replace("€", "").replace(",", ".").strip())
            except Exception:
                price_val = 0.0

            product = {
                "product_url": p.get("product_url", ""),
                "title": p.get("title", "N/A"),
                "image_url": p.get("image_url", ""),
                "price": p.get("price", "N/A"),
                "seller_name": p.get("seller_name", "N/A"),
                "delivery_time": p.get("delivery_time", "N/A"),
                "description": p.get("description", "N/A"),
                "brand": p.get("brand", "N/A"),
                "position": p.get("position"),
                "price_val": price_val,  # внутреннее поле для фильтрации
            }
            products.append(product)

        # Шаг 4: фильтрация по цене
        if min_price is not None or max_price is not None:
            products = [
                p for p in products
                if (min_price is None or p["price_val"] >= min_price)
                and (max_price is None or p["price_val"] <= max_price)
            ]

        # Шаг 5: формируем параметры поиска с total_products
        search_params = SearchParametersUsed(
            vin_recognized="WVWZZZ3CZLE073029",
            kba_recognized="0603/BRA",
            identified_part_type="Bremsbelag",
            vehicle_model=VehicleModel(
                brand_model="VW Passat B8 Variant (3G)",
                engine="2.0 TDI",
                kba_id="19080",
                url="https://www.autoteile-markt.de/shop/q-lamp/vw-passat-b8-variant-(3g)-2.0-tdi-ersatzteile-fi19080"
            ),
            total_products=len(products),
        )

        # Шаг 6: удаляем внутреннее поле price_val перед возвратом
        for p in products:
            p.pop("price_val", None)

        # Шаг 7: возвращаем Pydantic-объект
        return SearchResponse(
            status="ok",
            data=SearchResponseData(
                products=products,
                search_parameters_used=search_params
            )
        )
