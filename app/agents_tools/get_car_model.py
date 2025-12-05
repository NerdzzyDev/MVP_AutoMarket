import asyncio
import logging
from typing import Optional, Dict, Any

import aiohttp
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class AutoteileMarktAgent:
    """
    Агент для работы с Autoteile-Markt API по KBA (HSN/TSN).
    Делает:
      - запрос к API
      - парсит HTML из content
      - достаёт brand, model, engine, kba_id
      - строит URL
      - отдаёт search_code (последний сегмент URL)
    """

    API_URL = "https://www.autoteile-markt.de/api/vehicle/kba"

    def __init__(self, session: Optional[aiohttp.ClientSession] = None):
        # Можно передать внешний session (например, из FastAPI lifespan),
        # или агент сам создаст временный.
        self.session = session

    # ---------- Публичные методы ----------

    async def fetch_vehicle(self, hsn: str, tsn: str) -> Dict[str, Any]:
        """
        Вернёт dict вида:
        {
            "brand": "VW",
            "model": "Passat B8 Variant (3G)",
            "engine": "2.0 TDI",
            "kba_id": "19080",
            "url": "https://www.autoteile-markt.de/shop/q-lamp/...",
            "search_code": "vw-passat-b8-variant-(3g)-2.0-tdi-ersatzteile-fi19080",
        }
        """
        if not self.session:
            async with aiohttp.ClientSession() as session:
                return await self._fetch_with_session(session, hsn, tsn)
        else:
            return await self._fetch_with_session(self.session, hsn, tsn)

    def get_search_code(self, url: str) -> Optional[str]:
        """
        Вернёт всё после последнего слеша в URL:
        "https://.../vw-passat-b8-..." -> "vw-passat-b8-..."
        """
        if not url:
            return None

        cleaned = url.rstrip("/")  # убираем trailing /
        if not cleaned:
            return None

        return cleaned.rsplit("/", 1)[-1]

    # ---------- Внутренние методы ----------

    async def _fetch_with_session(
        self,
        session: aiohttp.ClientSession,
        hsn: str,
        tsn: str,
    ) -> Dict[str, Any]:
        payload = {
            "provider": "kumasoft",
            "type": "1",
            "hsn": hsn,
            "tsn": tsn,
        }

        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
            "Origin": "https://www.autoteile-markt.de",
            "Referer": "https://www.autoteile-markt.de/",
        }

        logger.info(f"[AutoteileMarktAgent] Fetching vehicle info for {hsn}/{tsn}")

        async with session.post(self.API_URL, data=payload, headers=headers) as resp:
            resp.raise_for_status()
            resp_json = await resp.json()

        content_html: str = resp_json.get("content", "") or ""
        if not content_html:
            logger.warning(
                "[AutoteileMarktAgent] Empty 'content' in response for %s/%s",
                hsn,
                tsn,
            )

        vehicle_info = self._parse_vehicle_html(content_html)

        # если kba_id не удалось достать из HTML — попробуем из JSON (если вдруг есть)
        if not vehicle_info.get("kba_id") and "kba_id" in resp_json:
            vehicle_info["kba_id"] = str(resp_json["kba_id"])

        # строим URL (если удалось собрать всё нужное)
        vehicle_info["url"] = self._build_vehicle_url(vehicle_info)

        # добавляем search_code
        vehicle_info["search_code"] = self.get_search_code(vehicle_info["url"])

        logger.debug("[AutoteileMarktAgent] Parsed vehicle_info: %r", vehicle_info)

        return vehicle_info

    def _parse_vehicle_html(self, html: str) -> Dict[str, Optional[str]]:
        """
        Парсит HTML такого вида:

        <div class="modal-body">
          <div class="row top5">
            <div class="col-sm-4">VW Passat B8 Variant (3G)</div>
            <div class="col-sm-2">2.0 TDI</div>
            <div class="col-sm-2">190 PS / 140 kW</div>
            <div class="col-sm-2">11.2014 - heute</div>
            <div class="col-sm-2 text-right">
              <button class="btn btn-amBlue" data-kbaselect="19080">Auswählen</button>
            </div>
          </div>
        </div>
        """

        soup = BeautifulSoup(html, "html.parser")

        row = soup.select_one("div.modal-body div.row.top5")
        if not row:
            logger.warning(
                "[AutoteileMarktAgent] row.top5 not found in HTML, raw html: %s",
                html[:500],
            )
            return {
                "brand": None,
                "model": None,
                "engine": None,
                "kba_id": None,
            }

        # 1) brand + model
        brand_model_div = row.find("div", class_="col-sm-4")
        brand_model_text = brand_model_div.get_text(strip=True) if brand_model_div else None

        brand: Optional[str] = None
        model: Optional[str] = None

        if brand_model_text:
            # "VW Passat B8 Variant (3G)" -> "VW", "Passat B8 Variant (3G)"
            parts = brand_model_text.split(" ", 1)
            if len(parts) == 2:
                brand, model = parts[0], parts[1]
            else:
                # на всякий случай, если разметка другая
                brand = brand_model_text

        # 2) engine (первый col-sm-2)
        col_sm2_list = row.find_all("div", class_="col-sm-2")
        engine: Optional[str] = None
        if len(col_sm2_list) >= 1:
            engine = col_sm2_list[0].get_text(strip=True)

        # 3) kba_id из data-kbaselect кнопки
        btn = row.select_one("button[data-kbaselect]")
        kba_id: Optional[str] = None
        if btn and btn.has_attr("data-kbaselect"):
            kba_id = btn["data-kbaselect"]

        return {
            "brand": brand,
            "model": model,
            "engine": engine,
            "kba_id": kba_id,
        }

    def _build_vehicle_url(self, vehicle_info: Dict[str, Any]) -> str:
        """
        Собирает URL в стиле:
        https://www.autoteile-markt.de/shop/q-lamp/vw-passat-b8-variant-(3g)-2.0-tdi-ersatzteile-fi19080

        Если чего-то не хватает — возвращает пустую строку.
        """
        brand = vehicle_info.get("brand")
        model = vehicle_info.get("model")
        engine = vehicle_info.get("engine")
        kba_id = vehicle_info.get("kba_id")

        if not all([brand, model, engine, kba_id]):
            logger.warning(
                "[AutoteileMarktAgent] Not enough data to build vehicle URL: %r",
                vehicle_info,
            )
            return ""

        # Примитивный slugify под текущий формат
        def slugify(s: str) -> str:
            return (
                s.lower()
                .replace(" ", "-")
                .replace("ä", "ae")
                .replace("ö", "oe")
                .replace("ü", "ue")
                .replace("ß", "ss")
            )

        brand_model_slug = slugify(f"{brand} {model}")
        engine_slug = slugify(engine)

        # q-lamp у тебя жестко в примере, если надо — вынеси в конфиг
        return (
            f"https://www.autoteile-markt.de/shop/q-lamp/"
            f"{brand_model_slug}-{engine_slug}-ersatzteile-fi{kba_id}"
        )


# --- Пример ручного запуска агента ---

async def _debug_main():
    async with aiohttp.ClientSession() as session:
        agent = AutoteileMarktAgent(session)
        # пример с 0603/BRA
        vehicle = await agent.fetch_vehicle("0603", "BRA")
        print(vehicle)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(_debug_main())
