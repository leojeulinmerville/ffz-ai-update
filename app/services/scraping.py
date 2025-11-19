from __future__ import annotations

import logging
from typing import Any, Dict, List
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from app.models import Subscription, User

logger = logging.getLogger(__name__)

REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

LEAGUE_SOURCES: Dict[str, Dict[str, Any]] = {
    "PL": {
        "name": "Premier League",
        "sources": [
            {"url": "https://www.bbc.com/sport/football/premier-league", "label": "BBC Sport"},
            {"url": "https://www.skysports.com/premier-league-news", "label": "Sky Sports"},
        ],
    },
    "FL1": {
        "name": "Ligue 1",
        "sources": [
            {"url": "https://www.bbc.com/sport/football/ligue-1", "label": "BBC Sport"},
            {"url": "https://www.skysports.com/ligue-1-news", "label": "Sky Sports"},
        ],
    },
    "CL": {
        "name": "Champions League",
        "sources": [
            {"url": "https://www.bbc.com/sport/football/champions-league", "label": "BBC Sport"},
            {"url": "https://www.uefa.com/uefachampionsleague/news/", "label": "UEFA"},
        ],
    },
}


def _get_league_config(code: str) -> Dict[str, Any]:
    code = (code or "").upper()
    return LEAGUE_SOURCES.get(code, {"name": code or "League", "sources": []})


def _extract_headlines(html: str, base_url: str, source_label: str) -> List[Dict[str, Any]]:
    soup = BeautifulSoup(html, "html.parser")
    results: List[Dict[str, Any]] = []
    seen: set[str] = set()

    def _try_add(title: str, href: str, summary: str | None) -> None:
        normalized = title.strip()
        if not normalized or len(normalized) < 6:
            return
        key = normalized.lower()
        if key in seen:
            return
        seen.add(key)
        full_url = urljoin(base_url, href)
        source_name = source_label or urlparse(full_url).netloc or "source"
        results.append(
            {
                "title": normalized,
                "summary": summary,
                "source": source_name,
                "url": full_url,
            }
        )

    heading_selectors = ["article h3", "article h2", "h3", "h2"]
    for selector in heading_selectors:
        for heading in soup.select(selector):
            title = heading.get_text(strip=True)
            link_tag = heading.find("a", href=True) or heading.find_parent("a", href=True)
            if not link_tag:
                continue
            href = link_tag.get("href")
            summary_tag = heading.find_next_sibling("p")
            summary_text = summary_tag.get_text(strip=True) if summary_tag else None
            _try_add(title, href, summary_text)
            if len(results) >= 8:
                return results

    if len(results) < 5:
        for anchor in soup.select("a[href]"):
            title = anchor.get_text(strip=True)
            href = anchor.get("href")
            if not href:
                continue
            summary_tag = anchor.find_next_sibling("p")
            summary_text = summary_tag.get_text(strip=True) if summary_tag else None
            _try_add(title, href, summary_text)
            if len(results) >= 8:
                break

    return results


def scrape_league_for_user(league_code: str, user: User) -> Dict[str, Any]:
    league_cfg = _get_league_config(league_code)
    favorite_team = (user.favorite_team or "").strip().lower()
    aggregated: List[Dict[str, Any]] = []
    favorite_mentions: List[Dict[str, Any]] = []
    sources_used: List[str] = []

    for source in league_cfg.get("sources", []):
        url = source["url"]
        try:
            resp = requests.get(url, headers=REQUEST_HEADERS, timeout=10)
            resp.raise_for_status()
            sources_used.append(url)
            headlines = _extract_headlines(resp.text, url, source.get("label", "source"))
            for headline in headlines:
                aggregated.append(headline)
                title_lower = headline["title"].lower()
                summary_lower = (headline.get("summary") or "").lower()
                if favorite_team and (favorite_team in title_lower or favorite_team in summary_lower):
                    favorite_mentions.append({"title": headline["title"], "url": headline["url"]})
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to scrape %s for league %s: %s", url, league_code, exc)

    deduped: List[Dict[str, Any]] = []
    seen_titles: set[str] = set()
    for item in aggregated:
        key = item["title"].lower()
        if key in seen_titles:
            continue
        seen_titles.add(key)
        deduped.append(item)

    return {
        "league_code": league_code,
        "league_name": league_cfg.get("name", league_code),
        "news_headlines": deduped[:10],
        "favorite_team_mentions": favorite_mentions,
        "sources_used": sources_used,
    }


def scrape_all_user_leagues(user: User, db: Session) -> Dict[str, Any]:
    subscriptions = (
        db.query(Subscription)
        .filter(Subscription.user_id == user.id, Subscription.is_active.is_(True))
        .all()
    )
    league_codes = sorted({sub.league_code.upper() for sub in subscriptions if sub.league_code})
    leagues: List[Dict[str, Any]] = []
    all_sources: List[str] = []

    for league_code in league_codes:
        league_data = scrape_league_for_user(league_code, user)
        leagues.append(league_data)
        for src in league_data.get("sources_used", []):
            if src not in all_sources:
                all_sources.append(src)

    return {
        "user": {
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "language": user.language,
            "favorite_team": user.favorite_team,
        },
        "leagues": leagues,
        "sources_used": all_sources,
    }
