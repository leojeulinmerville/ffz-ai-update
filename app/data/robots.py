import asyncio
from dataclasses import dataclass
from typing import Dict
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import httpx

from app.config import ALLOWED_DOMAINS

USER_AGENT = "FFZ-Scraper/1.0"
ROBOTS_CACHE: Dict[str, "RobotEntry"] = {}
ROBOTS_TTL_SECONDS = 3600


@dataclass
class RobotEntry:
    parser: RobotFileParser
    fetched_at: float


_lock = asyncio.Lock()


async def is_allowed(url: str) -> bool:
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    if not _is_domain_allowed(domain):
        return False

    async with _lock:
        entry = ROBOTS_CACHE.get(domain)
        if entry and (asyncio.get_event_loop().time() - entry.fetched_at) < ROBOTS_TTL_SECONDS:
            parser = entry.parser
        else:
            parser = await _fetch_parser(parsed.scheme, domain)
            ROBOTS_CACHE[domain] = RobotEntry(parser=parser, fetched_at=asyncio.get_event_loop().time())

    return parser.can_fetch(USER_AGENT, url)


def _is_domain_allowed(domain: str) -> bool:
    stripped = domain.lower()
    return any(stripped == allowed or stripped.endswith(f".{allowed}") for allowed in ALLOWED_DOMAINS)


async def _fetch_parser(scheme: str, domain: str) -> RobotFileParser:
    robots_url = f"{scheme}://{domain}/robots.txt"
    parser = RobotFileParser()
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(robots_url, headers={"User-Agent": USER_AGENT})
            if resp.status_code == 200:
                parser.parse(resp.text.splitlines())
            else:
                parser.parse(["User-agent: *", "Allow: /"])
    except httpx.HTTPError:
        parser.parse(["User-agent: *", "Allow: /"])
    return parser
