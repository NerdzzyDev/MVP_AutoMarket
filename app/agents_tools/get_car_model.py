import asyncio

import aiohttp
from app.utils.get_car_model import build_vehicle_url, parse_vehicle_html


# --- Класс агента ---
class AutoteileMarktAgent:
    API_URL = "https://www.autoteile-markt.de/api/vehicle/kba"

    def __init__(self, session=None):
        self.session = session

    async def fetch_vehicle(self, hsn: str, tsn: str) -> dict:
        """Возвращает словарь с полной маркой, движком, kba_id и ссылкой"""
        if not self.session:
            async with aiohttp.ClientSession() as session:
                return await self._fetch(session, hsn, tsn)
        else:
            return await self._fetch(self.session, hsn, tsn)

    async def _fetch(self, session, hsn: str, tsn: str) -> dict:
        data = {"provider": "kumasoft", "type": "1", "hsn": hsn, "tsn": tsn}
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
            "Origin": "https://www.autoteile-markt.de",
            "Referer": "https://www.autoteile-markt.de/",
        }

        async with session.post(self.API_URL, data=data, headers=headers) as resp:
            resp_json = await resp.json()

        vehicle_info = parse_vehicle_html(resp_json.get("content", ""))
        vehicle_info["url"] = build_vehicle_url(vehicle_info)
        return vehicle_info


# --- Пример использования ---
async def main():
    async with aiohttp.ClientSession() as session:
        agent = AutoteileMarktAgent(session)
        result = await agent.fetch_vehicle("0588", "act")
        print(result)


if __name__ == "__main__":
    asyncio.run(main())
