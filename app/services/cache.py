import time
from dataclasses import dataclass
from typing import Dict, Optional

from app.config import CACHE_TTL_SECONDS


@dataclass
class CacheEntry:
    value: str
    stored_at: float


_CACHE: Dict[str, CacheEntry] = {}


def build_cache_key(url: str, params: Optional[dict]) -> str:
    if not params:
        return url
    sorted_items = sorted(params.items())
    query = "&".join(f"{k}={v}" for k, v in sorted_items)
    return f"{url}?{query}"


def get_cached(url: str, params: Optional[dict] = None) -> Optional[str]:
    key = build_cache_key(url, params)
    entry = _CACHE.get(key)
    if not entry:
        return None
    if time.time() - entry.stored_at > CACHE_TTL_SECONDS:
        _CACHE.pop(key, None)
        return None
    return entry.value


def set_cached(url: str, params: Optional[dict], value: str) -> None:
    key = build_cache_key(url, params)
    _CACHE[key] = CacheEntry(value=value, stored_at=time.time())
