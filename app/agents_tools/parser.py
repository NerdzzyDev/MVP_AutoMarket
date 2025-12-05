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


class AutoteileMarktParserAgent:
    def __init__(self, redis_url="redis://redis:6379"):
        self.ua = UserAgent()
        self.redis = Redis(host="redis", port=6379, decode_responses=True)

    async def make_request(self, session, url):
        headers = {"User-Agent": self.ua.random}
        try:
            logger.debug(f"********* DEBUG! ********** MODEL LINK = {url}")
            async with session.get(url, headers=headers, timeout=10) as response:
                response.raise_for_status()
                return await response.text()
        except aiohttp.ClientError as e:
            print(f"Error fetching {url}: {e}")
            return None

    def decode_base64_url(self, encoded_href):
        try:
            return base64.b64decode(encoded_href).decode("utf-8")
        except (base64.binascii.Error, UnicodeDecodeError) as e:
            print(f"Error decoding Base64: {e}")
            return None

    def extract_product_urls(self, soup, max_products=10):
        cards = soup.find_all(
            "div", class_=lambda x: x and "card" in x and "itemRow" in x
        )
        if not cards:
            print("No product cards found")
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

        return products

    def extract_product_data(self, soup, product_url):
        product = {"product_url": product_url}

        product["title"] = (
            soup.find("h1").get_text(strip=True) if soup.find("h1") else "N/A"
        )

        carousel = soup.find("div", class_=lambda x: x and "carousel-inner" in x)
        product["image_url"] = (
            carousel.find("span", class_=lambda x: x and "zoomImg" in x)["href"]
            if carousel
            and carousel.find("span", class_=lambda x: x and "zoomImg" in x)
            and "href"
            in carousel.find("span", class_=lambda x: x and "zoomImg" in x).attrs
            else "N/A"
        )

        product["price"] = (
            soup.find("span", class_=lambda x: x and "supplierPrice" in x).get_text(
                strip=True
            )
            if soup.find("span", class_=lambda x: x and "supplierPrice" in x)
            else "N/A"
        )

        supplier_box = soup.find("div", class_=lambda x: x and "supplierBox" in x)
        product["seller_name"] = (
            supplier_box.find("a", attrs={"data-click": "infopage"}).get_text(
                strip=True
            )
            if supplier_box and supplier_box.find("a", attrs={"data-click": "infopage"})
            else "N/A"
        )

        part_info = soup.find("div", class_=lambda x: x and "partInfo" in x)
        product["delivery_time"] = (
            part_info.find("span", string=lambda x: x and "Lieferzeit" in x)
            .find_next_sibling(text=True)
            .strip()
            if part_info
            and part_info.find("span", string=lambda x: x and "Lieferzeit" in x)
            and part_info.find(
                "span", string=lambda x: x and "Lieferzeit" in x
            ).find_next_sibling(text=True)
            else "N/A"
        )

        product["description"] = (
            soup.find("div", id="partDescription").get_text(strip=True)
            if soup.find("div", id="partDescription")
            else "N/A"
        )

        return product

    async def fetch_product_details(self, session, product_urls):
        products = []
        for i, url in enumerate(product_urls):
            if i > 0:
                await asyncio.sleep(random.uniform(1, 2))

            html = await self.make_request(session, url)
            if not html:
                continue

            soup = BeautifulSoup(html, "lxml")
            product = self.extract_product_data(soup, url)
            products.append(product)

        return products

    def generate_cache_key(self, oem_number: str, max_products: int) -> str:
        raw_key = f"autoteile:{oem_number}:{max_products}"
        return hashlib.sha256(raw_key.encode()).hexdigest()

    async def get_total_products(self, session, oem_number, model_link=None):
        """Возвращает общее количество товаров по OEM"""
        if model_link:
            url = f"https://www.autoteile-markt.de/shop/q-{oem_number}/{model_link}"
        else:
            url = f"https://www.autoteile-markt.de/shop/q-{oem_number}/"

        html = await self.make_request(session, url)
        if not html:
            return 0

        soup = BeautifulSoup(html, "lxml")
        result_hit = soup.select_one("div.col-6.resultHits > b")
        if not result_hit:
            return 0

        # Извлекаем число и убираем точки
        total_str = result_hit.get_text(strip=True).split(" ")[0].replace(".", "")
        return int(total_str) if total_str.isdigit() else 0

    async def search_parts_by_oem(self, oem_number, max_products=10, model_link=None):
        cache_key = self.generate_cache_key(oem_number, max_products)

        # 🔍 Check cache
        cached = await self.redis.get(cache_key)
        if cached:
            print(f"🔁 Cache hit for OEM {oem_number}")
            return cached

        if model_link:
            url = f"https://www.autoteile-markt.de/shop/q-{oem_number}/{model_link}"
        else:
            url = f"https://www.autoteile-markt.de/shop/q-{oem_number}/"

        # If not cached, scrape
        async with aiohttp.ClientSession() as session:
            # url = f"https://www.autoteile-markt.de/shop/q-{oem_number}"
            html = await self.make_request(session, url)
            if not html:
                return json.dumps({"products": []}, ensure_ascii=False, indent=2)

            soup = BeautifulSoup(html, "lxml")
            product_urls = [
                p["product_url"]
                for p in self.extract_product_urls(soup, max_products)
                if p["product_url"] != "N/A"
            ]

            if not product_urls:
                print("No valid product URLs")
                return json.dumps({"products": []}, ensure_ascii=False, indent=2)

            products = await self.fetch_product_details(session, product_urls)
            result = json.dumps({"products": products}, ensure_ascii=False, indent=2)

            # Cache for 24 hours
            await self.redis.set(cache_key, result, ex=60 * 60 * 24)
            print(f"✅ Cached result for OEM {oem_number}")

            return result
