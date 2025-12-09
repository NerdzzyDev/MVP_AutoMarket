import asyncio
import base64
import hashlib
import json
import random

import aiohttp
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from loguru import logger
from redis.asyncio import Redis

from app.schemas.search import Brand


class AutoteileMarktParserAgent:
    def __init__(self, redis_url: str = "redis://redis:6379"):
        self.ua = UserAgent()
        # redis_url пока не используешь, но оставим на будущее
        self.redis = Redis(host="redis", port=6379, decode_responses=True)
        logger.info("[Parser] AutoteileMarktParserAgent initialized with Redis %s", redis_url)

    # ===================== Вспомогалки =====================

    async def make_request(self, session: aiohttp.ClientSession, url: str) -> str | None:
        headers = {"User-Agent": self.ua.random}
        try:
            logger.info("[Parser] HTTP GET %s", url)
            async with session.get(url, headers=headers, timeout=10) as response:
                response.raise_for_status()
                text = await response.text()
                logger.debug("[Parser] Got %d bytes from %s", len(text), url)
                return text
        except aiohttp.ClientError as e:
            logger.error("[Parser] Error fetching %s: %s", url, e)
            return None

    def decode_base64_url(self, encoded_href: str) -> str | None:
        try:
            decoded = base64.b64decode(encoded_href).decode("utf-8")
            logger.debug("[Parser] Decoded Base64 href: %s -> %s", encoded_href, decoded)
            return decoded
        except (base64.binascii.Error, UnicodeDecodeError) as e:
            logger.error("[Parser] Error decoding Base64 href %s: %s", encoded_href, e)
            return None

    def brand_to_slug(self, brand: Brand) -> str:
        """
        Преобразует Brand в slug, используемый в URL вида /shop/h-{slug}/q-...
        """
        overrides = {
            Brand.Febi_Bilstein: "febi-bilstein",
        }
        if brand in overrides:
            slug = overrides[brand]
        else:
            slug = brand.value.lower().replace(" ", "-")

        logger.debug("[Parser] Brand %s -> slug %s", brand.value, slug)
        return slug

    def generate_cache_key(
        self,
        oem_number: str,
        max_products: int,
        model_link: str | None = None,
        brand: Brand | None = None,
    ) -> str:
        raw_key = f"autoteile:oem={oem_number}:max={max_products}"
        if model_link:
            raw_key += f":model={model_link}"
        if brand:
            raw_key += f":brand={brand.value}"
        cache_key = hashlib.sha256(raw_key.encode()).hexdigest()
        logger.debug("[Parser] Generated cache key: raw=%s -> %s", raw_key, cache_key)
        return cache_key

    # ===================== Парсинг HTML =====================

    def extract_product_urls(self, soup: BeautifulSoup, max_products: int = 10) -> list[dict]:
        cards = soup.find_all(
            "div", class_=lambda x: x and "card" in x and "itemRow" in x
        )
        if not cards:
            logger.warning("[Parser] No product cards found on listing page")
            return []

        products = []
        for card in cards[:max_products]:
            title_elem = card.find(
                lambda tag: tag.name in ["a", "span"]
                and tag.get("class")
                and "card-title" in tag.get("class")
                and "itemTitle" in tag.get("class")
            )
            if not title_elem:
                continue

            url = "N/A"
            if title_elem.name == "a" and "href" in title_elem.attrs:
                url = f"https://www.autoteile-markt.de{title_elem['href']}"
            elif "data-href64" in title_elem.attrs:
                decoded_href = self.decode_base64_url(title_elem["data-href64"])
                if decoded_href:
                    url = f"https://www.autoteile-markt.de{decoded_href}"

            products.append({"product_url": url})

        logger.info("[Parser] Extracted %d product URLs (max=%d)", len(products), max_products)
        return products

    def extract_product_data(self, soup: BeautifulSoup, product_url: str) -> dict:
        product: dict[str, str] = {"product_url": product_url}

        title_tag = soup.find("h1")
        product["title"] = title_tag.get_text(strip=True) if title_tag else "N/A"

        carousel = soup.find("div", class_=lambda x: x and "carousel-inner" in x)
        img_span = (
            carousel.find("span", class_=lambda x: x and "zoomImg" in x)
            if carousel
            else None
        )
        product["image_url"] = (
            img_span["href"] if img_span and "href" in img_span.attrs else "N/A"
        )

        price_tag = soup.find("span", class_=lambda x: x and "supplierPrice" in x)
        product["price"] = price_tag.get_text(strip=True) if price_tag else "N/A"

        supplier_box = soup.find("div", class_=lambda x: x and "supplierBox" in x)
        supplier_link = (
            supplier_box.find("a", attrs={"data-click": "infopage"})
            if supplier_box
            else None
        )
        product["seller_name"] = (
            supplier_link.get_text(strip=True) if supplier_link else "N/A"
        )

        part_info = soup.find("div", class_=lambda x: x and "partInfo" in x)
        delivery_label = (
            part_info.find("span", string=lambda x: x and "Lieferzeit" in x)
            if part_info
            else None
        )
        if delivery_label:
            sibling = delivery_label.find_next_sibling(text=True)
            product["delivery_time"] = sibling.strip() if sibling else "N/A"
        else:
            product["delivery_time"] = "N/A"

        desc_div = soup.find("div", id="partDescription")
        product["description"] = desc_div.get_text(strip=True) if desc_div else "N/A"

        logger.debug("[Parser] Parsed product data from %s: %s", product_url, product)
        return product

    async def fetch_product_details(
        self, session: aiohttp.ClientSession, product_urls: list[str]
    ) -> list[dict]:
        products: list[dict] = []
        logger.info("[Parser] Fetching details for %d products", len(product_urls))

        for i, url in enumerate(product_urls):
            if i > 0:
                delay = random.uniform(1, 2)
                logger.debug("[Parser] Sleeping %.2f seconds before next product request", delay)
                await asyncio.sleep(delay)

            html = await self.make_request(session, url)
            if not html:
                logger.warning("[Parser] Empty HTML for product URL: %s", url)
                continue

            soup = BeautifulSoup(html, "lxml")
            product = self.extract_product_data(soup, url)
            products.append(product)

        logger.info("[Parser] Total fetched product details: %d", len(products))
        return products

    # ===================== High-level методы =====================

    async def get_total_products(
        self,
        session: aiohttp.ClientSession,
        oem_number: str,
        model_link: str | None = None,
        brand: Brand | None = None,
    ) -> int:
        """Возвращает общее количество товаров по OEM (опционально с брендом)."""
        base = "https://www.autoteile-markt.de/shop"
        path_parts = []

        if brand:
            brand_slug = self.brand_to_slug(brand)
            path_parts.append(f"h-{brand_slug}")

        path_parts.append(f"q-{oem_number}")

        if model_link:
            path_parts.append(model_link)

        url = f"{base}/" + "/".join(path_parts)
        logger.info("[Parser] get_total_products: URL=%s", url)

        html = await self.make_request(session, url)
        if not html:
            logger.warning("[Parser] get_total_products: empty HTML for %s", url)
            return 0

        soup = BeautifulSoup(html, "lxml")
        result_hit = soup.select_one("div.col-6.resultHits > b")
        if not result_hit:
            logger.warning("[Parser] get_total_products: resultHits not found for %s", url)
            return 0

        total_str = result_hit.get_text(strip=True).split(" ")[0].replace(".", "")
        total = int(total_str) if total_str.isdigit() else 0
        logger.info("[Parser] get_total_products: %d products for %s", total, url)
        return total

    async def search_parts_by_oem(
        self,
        oem_number: str,
        max_products: int = 10,
        model_link: str | None = None,
        brand: Brand | None = None,
    ) -> str:
        """
        Основной метод поиска:
        - oem_number: то, что ты передаёшь как search_code/код;
        - model_link: хвост с моделью, если нужен;
        - brand: опциональный фильтр по бренду.
        Возвращает JSON-строку вида {"products": [...]}.
        """
        cache_key = self.generate_cache_key(
            oem_number=oem_number,
            max_products=max_products,
            model_link=model_link,
            brand=brand,
        )

        # 🔍 Check cache
        cached = await self.redis.get(cache_key)
        if cached:
            logger.info(
                "[Parser] Cache HIT for OEM=%r, brand=%r, model_link=%r",
                oem_number,
                brand.value if brand else None,
                model_link,
            )
            return cached

        base = "https://www.autoteile-markt.de/shop"
        path_parts = []

        if brand:
            brand_slug = self.brand_to_slug(brand)
            path_parts.append(f"h-{brand_slug}")

        path_parts.append(f"q-{oem_number}")

        if model_link:
            path_parts.append(model_link)

        url = f"{base}/" + "/".join(path_parts)
        logger.info(
            "[Parser] search_parts_by_oem: URL=%s (OEM=%r, brand=%r, max_products=%d)",
            url,
            oem_number,
            brand.value if brand else None,
            max_products,
        )

        # If not cached, scrape
        async with aiohttp.ClientSession() as session:
            html = await self.make_request(session, url)
            if not html:
                logger.warning("[Parser] Empty HTML for listing URL: %s", url)
                empty_result = json.dumps({"products": []}, ensure_ascii=False, indent=2)
                return empty_result

            soup = BeautifulSoup(html, "lxml")
            raw_urls = self.extract_product_urls(soup, max_products)
            product_urls = [p["product_url"] for p in raw_urls if p["product_url"] != "N/A"]

            logger.info(
                "[Parser] search_parts_by_oem: extracted %d product URLs from %s",
                len(product_urls),
                url,
            )

            if not product_urls:
                logger.warning("[Parser] No valid product URLs for listing URL: %s", url)
                empty_result = json.dumps({"products": []}, ensure_ascii=False, indent=2)
                # можно тоже закэшировать пустой ответ, но аккуратно
                await self.redis.set(cache_key, empty_result, ex= 60 * 60 * 24 * 30)
                return empty_result

            products = await self.fetch_product_details(session, product_urls)
            result = json.dumps({"products": products}, ensure_ascii=False, indent=2)

            # Cache for 24 hours
            CACHE_TTL_MONTH = 60 * 60 * 24 * 30  # 30 дней
            await self.redis.set(cache_key, result, ex=CACHE_TTL_MONTH)
            logger.info(
                "[Parser] Cached result for OEM=%r, brand=%r, model_link=%r (products=%d)",
                oem_number,
                brand.value if brand else None,
                model_link,
                len(products),
            )

            return result

    async def search_parts_by_oem_and_brand(
        self,
        oem_number: str,
        brand: Brand,
        max_products: int = 10,
        model_link: str | None = None,
    ) -> str:
        """
        Обёртка над search_parts_by_oem с обязательным brand.
        """
        logger.info(
            "[Parser] search_parts_by_oem_and_brand: OEM=%r, brand=%r, model_link=%r, max_products=%d",
            oem_number,
            brand.value,
            model_link,
            max_products,
        )
        return await self.search_parts_by_oem(
            oem_number=oem_number,
            max_products=max_products,
            model_link=model_link,
            brand=brand,
        )
