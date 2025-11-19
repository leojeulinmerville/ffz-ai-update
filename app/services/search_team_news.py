from __future__ import annotations

import logging
from typing import Any, Dict, List
from urllib.parse import quote_plus, urljoin, urlparse

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

SEARCH_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

SEARCH_URL = "https://www.bing.com/search?q={query}"


def search_team_news(query: str, max_items: int = 5) -> List[Dict[str, Any]]:
    if not query:
        return []

    url = SEARCH_URL.format(query=quote_plus(query))
    results: List[Dict[str, Any]] = []
    seen_titles: set[str] = set()

    try:
        resp = requests.get(url, headers=SEARCH_HEADERS, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        for li in soup.select("li.b_algo"):
            heading = li.find("h2")
            if not heading:
                continue
            link = heading.find("a", href=True)
            if not link:
                continue
            title = link.get_text(" ", strip=True)
            normalized = title.strip()
            if not normalized:
                continue
            key = normalized.lower()
            if key in seen_titles:
                continue
            href = link["href"]
            snippet = li.find("p")
            summary = snippet.get_text(" ", strip=True) if snippet else None
            parsed = urlparse(href)
            source = parsed.netloc.replace("www.", "") if parsed.netloc else "source"
            results.append(
                {
                    "title": normalized,
                    "summary": summary,
                    "source": source,
                    "url": urljoin(url, href),
                    "published_at": None,
                }
            )
            seen_titles.add(key)
            if len(results) >= max_items:
                break
    except Exception as exc:  # noqa: BLE001
        logger.warning("Team news search failed for %s: %s", query, exc)
        return []

    return results
