import asyncio
import random
import csv
import base64
from bs4 import BeautifulSoup
import aiohttp
from loguru import logger

# --- Конфиг ---
MAX_PRODUCTS = 3
CSV_FILE = "products.csv"

logger.add(lambda msg: print(msg, end=""))

async def fetch_html(session, url):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    logger.debug(f"Fetching URL: {url}")
    try:
        async with session.get(url, headers=headers, timeout=10) as resp:
            resp.raise_for_status()
            html = await resp.text()
            logger.debug(f"Fetched {len(html)} characters from {url}")
            return html
    except Exception as e:
        logger.error(f"Error fetching {url}: {e}")
        return None

def decode_base64_url(encoded_href):
    try:
        return base64.b64decode(encoded_href).decode("utf-8")
    except Exception as e:
        logger.warning(f"Failed to decode base64 {encoded_href}: {e}")
        return None

def extract_product_urls(html, max_products=MAX_PRODUCTS):
    soup = BeautifulSoup(html, "lxml")
    cards = soup.find_all("div", class_=lambda x: x and "card" in x and "itemRow" in x)
    logger.debug(f"Found {len(cards)} product cards on page")
    urls = []
    for i, card in enumerate(cards[:max_products]):
        title_elem = card.find(lambda tag: tag.name in ["a","span"] 
                               and tag.get("class") 
                               and "card-title" in tag.get("class") 
                               and "itemTitle" in tag.get("class"))
        url = "N/A"
        if title_elem:
            if title_elem.name == "a" and "href" in title_elem.attrs:
                url = f"https://www.autoteile-markt.de{title_elem['href']}"
            elif "data-href64" in title_elem.attrs:
                decoded = decode_base64_url(title_elem["data-href64"])
                if decoded:
                    url = f"https://www.autoteile-markt.de{decoded}"
        if url == "N/A":
            logger.warning(f"{i+1}: No valid link found in card")
        else:
            urls.append(url)
    return urls

def extract_product_data(html, url):
    soup = BeautifulSoup(html, "lxml")
    product = {"product_url": url}
    product["title"] = soup.find("h1").get_text(strip=True) if soup.find("h1") else "N/A"

    # Изображение
    carousel = soup.find("div", class_=lambda x: x and "carousel-inner" in x)
    img_tag = carousel.find("span", class_=lambda x: x and "zoomImg" in x) if carousel else None
    product["image_url"] = img_tag["href"] if img_tag and "href" in img_tag.attrs else "N/A"

    # Цена
    price_tag = soup.find("span", class_=lambda x: x and "supplierPrice" in x)
    product["price"] = price_tag.get_text(strip=True) if price_tag else "N/A"

    # Продавец
    supplier_box = soup.find("div", class_=lambda x: x and "supplierBox" in x)
    seller_tag = supplier_box.find("a", attrs={"data-click": "infopage"}) if supplier_box else None
    product["seller_name"] = seller_tag.get_text(strip=True) if seller_tag else "N/A"

    # Срок доставки
    part_info = soup.find("div", class_=lambda x: x and "partInfo" in x)
    delivery_tag = part_info.find("span", string=lambda x: x and "Lieferzeit" in x) if part_info else None
    product["delivery_time"] = delivery_tag.find_next_sibling(text=True).strip() if delivery_tag and delivery_tag.find_next_sibling(text=True) else "N/A"

    # Описание
    desc_tag = soup.find("div", id="partDescription")
    product["description"] = desc_tag.get_text(strip=True) if desc_tag else "N/A"

    return product

async def scrape_products(url):
    async with aiohttp.ClientSession() as session:
        html = await fetch_html(session, url)
        if not html:
            return []

        product_urls = extract_product_urls(html)
        if not product_urls:
            logger.warning("No product URLs found on main page")
            return []

        products = []
        for i, u in enumerate(product_urls):
            await asyncio.sleep(random.uniform(1, 2))
            html_detail = await fetch_html(session, u)
            if html_detail:
                product = extract_product_data(html_detail, u)
                products.append(product)
                logger.debug(f"Scraped product: {product['title']}")
        return products

def save_to_csv(products, filename=CSV_FILE):
    if not products:
        logger.warning("No products to save")
        return
    keys = products[0].keys()
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(products)
    logger.success(f"Saved {len(products)} products to {filename}")

# --- Main ---
if __name__ == "__main__":
    url = "https://www.autoteile-markt.de/shop/q-lamp/vw-passat-b8-variant-(3g)-2.0-tdi-ersatzteile-fi19080"  # <-- твой URL
    products = asyncio.run(scrape_products(url))
    save_to_csv(products)
