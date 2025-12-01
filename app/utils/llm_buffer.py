import time


# ==== TEMPORARY STORAGE (BUFFER) ====
class TempStorage:
    def __init__(self):
        self.store = {}

    def put(self, key: str, value: bytes, ttl: int = 300):
        self.store[key] = (value, time.time() + ttl)

    def get(self, key: str) -> bytes | None:
        value = self.store.get(key)
        if not value:
            return None
        data, expires_at = value
        if time.time() > expires_at:
            del self.store[key]
            return None
        return data

    def pop(self, key: str) -> bytes | None:
        data = self.get(key)
        if key in self.store:
            del self.store[key]
        return data


temp_storage = TempStorage()