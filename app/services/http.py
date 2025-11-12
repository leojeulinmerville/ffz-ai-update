import asyncio
import random
from typing import Any, Dict, Optional

import httpx
from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.config import PROXY_URL
from app.data.robots import is_allowed
from app.services.cache import get_cached, set_cached

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/129.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/129.0 Safari/537.36",
]

_client_lock = asyncio.Lock()
_client: Optional[httpx.AsyncClient] = None


async def _get_client() -> httpx.AsyncClient:
    global _client
    async with _client_lock:
        if _client is None:
            _client = httpx.AsyncClient(
                timeout=10.0,
                follow_redirects=True,
                proxies=PROXY_URL,
            )
        return _client


async def fetch_text(
    url: str,
    *,
    params: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    cache: bool = True,
    force_refresh: bool = False,
) -> str:
    if not await is_allowed(url):
        raise PermissionError(f"Robots policy forbids scraping {url}")

    if cache and not force_refresh:
        cached = get_cached(url, params)
        if cached:
            return cached

    merged_headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
    }
    if headers:
        merged_headers.update(headers)

    client = await _get_client()

    async for attempt in AsyncRetrying(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=8),
        retry=retry_if_exception_type(httpx.HTTPError),
    ):
        with attempt:
            response = await client.get(url, params=params, headers=merged_headers)
            response.raise_for_status()
            html = response.text

    if cache:
        set_cached(url, params, html)
    return html
