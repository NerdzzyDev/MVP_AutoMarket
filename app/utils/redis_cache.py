# app/utils/redis_cache.py
import json
import os

import redis.asyncio as redis

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")  # ✅ только один раз порт
CACHE_TTL = 60 * 60 * 24  # 24 часа

redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)


def normalize(value: str | None) -> str:
    return value.lower() if value else "unknown"


async def get_cached_oem(part_query: str) -> list[str] | None:
    key = f"oem:{normalize(part_query)}"
    cached = await redis_client.get(key)
    if cached:
        return json.loads(cached)
    return None


async def set_cached_oem(part_query: str, data: list[str]):
    key = f"oem:{normalize(part_query)}"
    await redis_client.set(key, json.dumps(data), ex=CACHE_TTL)