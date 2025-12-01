from bs4 import BeautifulSoup

# --- Утилиты  AutoteileMarktAgent (для получения модели по kba tsn)---


def parse_vehicle_html(html: str) -> dict:
    """Парсит HTML из content и возвращает данные авто и kba_id"""
    soup = BeautifulSoup(html, "lxml")
    row = soup.find("div", class_="row top5")
    if not row:
        return {}

    brand_model = row.find("div", class_="col-sm-4").get_text(strip=True)
    engine = row.find("div", class_="col-sm-2").get_text(strip=True)
    button = row.find("button", {"data-kbaselect": True})
    kba_id = button["data-kbaselect"] if button else None
    return {"brand_model": brand_model, "engine": engine, "kba_id": kba_id}


def build_vehicle_url(vehicle: dict) -> str:
    """Формирует ссылку на детали авто на сайте autoteile-markt.de"""
    if not vehicle.get("kba_id"):
        return None
    brand_model_slug = vehicle["brand_model"].lower().replace(" ", "-")
    engine_slug = vehicle["engine"].lower().replace(" ", "-")
    return (
        f"https://www.autoteile-markt.de/shop/q-lamp/{brand_model_slug}-{engine_slug}-ersatzteile-fi{vehicle['kba_id']}"
    )