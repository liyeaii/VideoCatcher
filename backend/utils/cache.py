import hashlib
import time
from typing import Any, Optional


class TTLCache:
    """Simple in-memory TTL cache with automatic expiry."""

    def __init__(self, ttl_seconds: int = 1800):
        self._cache: dict[str, tuple[Any, float]] = {}
        self._ttl = ttl_seconds

    def _hash_key(self, raw_key: str) -> str:
        return hashlib.sha256(raw_key.encode()).hexdigest()[:16]

    def get(self, key: str) -> Optional[Any]:
        hashed = self._hash_key(key)
        entry = self._cache.get(hashed)
        if entry is None:
            return None
        value, expiry = entry
        if time.time() > expiry:
            del self._cache[hashed]
            return None
        return value

    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None):
        hashed = self._hash_key(key)
        ttl = ttl_seconds if ttl_seconds is not None else self._ttl
        self._cache[hashed] = (value, time.time() + ttl)

    def invalidate(self, key: str):
        hashed = self._hash_key(key)
        self._cache.pop(hashed, None)

    def clear(self):
        self._cache.clear()
