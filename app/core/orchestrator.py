from typing import Optional, List
import json
import logging

from app.agents_tools.parser import AutoteileMarktParserAgent
from app.agents_tools.part_text import TextPartIdentifierAgent
from app.schemas.search import (
    SearchResponse,
    SearchResponseData,
    SearchParametersUsed,
    VehicleModel,
    PartPosition,
    Brand,
)

logger = logging.getLogger(__name__)


class PartSearchOrchestrator:
    def __init__(self):
        self.text_agent = TextPartIdentifierAgent()
        self.parser_agent = AutoteileMarktParserAgent()
        self.mock_search_code = "vw-passat-b8-variant-(3g)-2.0-tdi-ersatzteile-fi19080"

    async def search(
        self,
        search_code: str,
        query_text: str,
        position_flag: Optional[str] = None,
        max_products: int = 10,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        brand_filter: Optional[List[Brand]] = None,
    ) -> SearchResponse:
        # ===== Шаг 0. Входные параметры =====
        logger.info(
            "[PartSearch] Start search: "
            f"search_code={search_code!r}, query_text={query_text!r}, "
            f"position_flag={position_flag}, brand_filter={brand_filter}, "
            f"max_products={max_products}, min_price={min_price}, max_price={max_price}"
        )

        # ===== Шаг 1. Нормализация запроса (определяем OEM по тексту) =====
        normalized_query = await self.text_agent.normalize_query(query_text, position_flag)
        logger.info(
            "[PartSearch] Normalized query_text → OEM: %r → %r",
            query_text,
            normalized_query,
        )
        logger.debug(
            "[PartSearch] Normalization context: position_flag=%r", position_flag
        )

        # ===== Шаг 2. Поход к парсеру (AutoteileMarktParserAgent) =====
        search_results: list[tuple[object, str]] = []  # (brand_tag, json_str)

        logger.info("[PartSearch] Brand filter at parser step: %r", brand_filter)

        if not brand_filter:
            # Без бренда — старый сценарий
            logger.info(
                "[PartSearch] No brand filter → using search_parts_by_oem "
                "with model_link=%r",
                search_code or self.mock_search_code,
            )
            search_result_json = await self.parser_agent.search_parts_by_oem(
                oem_number=normalized_query,
                max_products=max_products,
                model_link=search_code or self.mock_search_code,
            )
            logger.debug(
                "[PartSearch] Raw search_result_json (no brand, first 500 chars): %s",
                (search_result_json[:500] + "...") if search_result_json and len(search_result_json) > 500 else search_result_json,
            )
            search_results.append(("ALL", search_result_json))
        else:
            # С брендами — по одному запросу на каждый
            logger.info(
                "[PartSearch] Brand filter is set, querying per brand: %s",
                ", ".join(b.value for b in brand_filter),
            )
            for brand in brand_filter:
                try:
                    logger.info(
                        "[PartSearch] → search_parts_by_oem_and_brand for OEM=%r, brand=%r, model_link=%r",
                        normalized_query,
                        brand.value,
                        search_code or self.mock_search_code,
                    )
                    search_result_json = await self.parser_agent.search_parts_by_oem_and_brand(
                        oem_number=normalized_query,
                        brand=brand,
                        max_products=max_products,
                        model_link=search_code or self.mock_search_code,
                    )
                    logger.debug(
                        "[PartSearch] Raw search_result_json for brand=%s (first 500 chars): %s",
                        brand.value,
                        (search_result_json[:500] + "...") if search_result_json and len(search_result_json) > 500 else search_result_json,
                    )
                    search_results.append((brand, search_result_json))
                except Exception:
                    logger.exception(
                        "[PartSearch] Error while searching parts for OEM=%r, brand=%r",
                        normalized_query,
                        brand.value,
                    )

        # ===== Шаг 3. Собираем все продукты =====
        products: list[dict] = []

        for brand_tag, search_result_json in search_results:
            if not search_result_json:
                logger.warning(
                    "[PartSearch] Empty search_result_json for brand_tag=%r", brand_tag
                )
                continue

            try:
                search_result = json.loads(search_result_json or "{}")
            except json.JSONDecodeError:
                logger.exception(
                    "[PartSearch] Failed to decode search_result_json for brand_tag=%r",
                    brand_tag,
                )
                continue

            raw_products = search_result.get("products", [])
            logger.info(
                "[PartSearch] Parsed %d raw products for brand_tag=%r",
                len(raw_products),
                brand_tag,
            )

            for p in raw_products:
                raw_price = p.get("price", "0")
                try:
                    price_val = float(
                        raw_price.replace("€", "").replace(",", ".").strip()
                    )
                except Exception:
                    logger.debug(
                        "[PartSearch] Failed to parse price %r, fallback to 0.0",
                        raw_price,
                    )
                    price_val = 0.0

                # Определяем бренд продукта
                if isinstance(brand_tag, Brand):
                    product_brand = p.get("brand") or brand_tag.value
                else:
                    product_brand = p.get("brand", "N/A")

                product = {
                    "product_url": p.get("product_url", ""),
                    "title": p.get("title", "N/A"),
                    "image_url": p.get("image_url", ""),
                    "price": raw_price or "N/A",
                    "seller_name": p.get("seller_name", "N/A"),
                    "delivery_time": p.get("delivery_time", "N/A"),
                    "description": p.get("description", "N/A"),
                    "brand": product_brand,
                    "position": p.get("position"),
                    "price_val": price_val,  # внутреннее поле для фильтрации
                }
                products.append(product)

        logger.info("[PartSearch] Total products before filters: %d", len(products))

        # ===== Шаг 4. Фильтрация по цене =====
        if min_price is not None or max_price is not None:
            before_count = len(products)
            products = [
                p
                for p in products
                if (min_price is None or p["price_val"] >= min_price)
                and (max_price is None or p["price_val"] <= max_price)
            ]
            logger.info(
                "[PartSearch] Price filter applied: min_price=%s, max_price=%s, "
                "products: %d → %d",
                min_price,
                max_price,
                before_count,
                len(products),
            )

        # ===== Шаг 5. Параметры поиска (что именно мы делали) =====
        if not brand_filter:
            brand_model_value = "Any"
        elif len(brand_filter) == 1:
            brand_model_value = brand_filter[0].value
        else:
            brand_model_value = ", ".join(b.value for b in brand_filter)

        logger.info(
            "[PartSearch] Building SearchParametersUsed: "
            "vin_recognized=%r, kba_recognized=%r, identified_part_type=%r, brand_model=%r, total_products=%d",
            search_code,
            search_code,
            normalized_query,
            brand_model_value,
            len(products),
        )

        search_params = SearchParametersUsed(
            vin_recognized=search_code,
            kba_recognized=search_code,
            identified_part_type=normalized_query,
            vehicle_model=VehicleModel(
                brand_model=brand_model_value,
                engine="",
                kba_id="",
                url=f"https://www.autoteile-markt.de/shop/q-{normalized_query}/{self.mock_search_code}",
            ),
            total_products=len(products),
        )

        # ===== Шаг 6. Чистим внутренние поля =====
        for p in products:
            p.pop("price_val", None)

        # ===== Шаг 7. Финальный лог и возврат =====
        logger.info(
            "[PartSearch] Search finished. Final products=%d, "
            "vin_recognized=%r, kba_recognized=%r, brand_model=%r",
            len(products),
            search_params.vin_recognized,
            search_params.kba_recognized,
            search_params.vehicle_model.brand_model,
        )

        return SearchResponse(
            status="ok",
            data=SearchResponseData(
                products=products,
                search_parameters_used=search_params,
            ),
        )
