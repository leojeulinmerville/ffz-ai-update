from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from app.models import Subscription, User
from app.services.search_team_news import search_team_news

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

LEAGUES: Dict[str, Dict[str, Any]] = {
    "PL": {
        "code": "PL",
        "name": "Premier League",
        "table_url": "https://www.bbc.com/sport/football/premier-league/table",
        "news_url": "https://www.bbc.com/sport/football/premier-league",
        "extra_news_urls": [
            "https://www.skysports.com/premier-league-news",
            "https://www.premierleague.com/news",
        ],
    },
    "FL1": {
        "code": "FL1",
        "name": "Ligue 1",
        # nouvelles URLs BBC (les anciennes /ligue-1 renvoient 404)
        "table_url": "https://www.bbc.com/sport/football/french-ligue-one/table",
        "news_url": "https://www.bbc.com/sport/football/french-ligue-one",
        "extra_news_urls": [
            "https://www.skysports.com/ligue-1-news",
            "https://www.ligue1.com/ligue1-ubereats",
        ],
    },
    "CL": {
        "code": "CL",
        "name": "Champions League",
        "table_url": "https://www.bbc.com/sport/football/champions-league/table",
        "news_url": "https://www.bbc.com/sport/football/champions-league",
        "extra_news_urls": [
            "https://www.skysports.com/champions-league-news",
            "https://www.uefa.com/uefachampionsleague/news/",
        ],
    },
}


def _to_int(value: str | None) -> Optional[int]:
    if value is None:
        return None
    try:
        cleaned = "".join(ch for ch in value if ch.isdigit() or ch == "-")
        return int(cleaned)
    except Exception:
        return None


def clean_headline_text(raw: str | None) -> str:
    if not raw:
        return ""
    text = raw.strip()
    timestamp_pattern = re.compile(
        r"^\d{1,2}:\d{2}\s*(?:GMT|BST)?\s*\d{1,2}\s+[A-Za-z]+(?:\s+\d{4})?\s*",
        re.IGNORECASE,
    )
    text = timestamp_pattern.sub("", text)
    text = re.sub(r"(?i)^published\s+at\s+", "", text)
    text = re.sub(r"(?i)\bpublished\s+at\s+\d{1,2}:\d{2}.*", "", text)
    text = " ".join(text.split())
    return text


def fetch_table_top(table_url: str, max_teams: int = 8) -> List[Dict[str, Any]]:
    try:
        resp = requests.get(table_url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to fetch table %s: %s", table_url, exc)
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    rows = soup.select("table tbody tr") or soup.select("table tr")
    table_top: List[Dict[str, Any]] = []

    for row in rows:
        cells = row.find_all(["td", "th"])
        if len(cells) < 4:
            continue
        try:
            rank = _to_int(cells[0].get_text(strip=True))
            team = cells[1].get_text(" ", strip=True)
            played = _to_int(cells[2].get_text(strip=True))
            points = _to_int(cells[-1].get_text(strip=True))
            goals_for = None
            goals_against = None
            if len(cells) >= 9:
                goals_for = _to_int(cells[6].get_text(strip=True))
                goals_against = _to_int(cells[7].get_text(strip=True))
            elif len(cells) >= 7:
                goals_for = _to_int(cells[4].get_text(strip=True))
                goals_against = _to_int(cells[5].get_text(strip=True))
            if (
                not rank
                or not team
                or not any(ch.isalpha() for ch in team)
                or points is None
            ):
                continue
            table_top.append(
                {
                    "rank": rank,
                    "team": team,
                    "played": played or 0,
                    "points": points or 0,
                    "goals_for": goals_for,
                    "goals_against": goals_against,
                }
            )
            if len(table_top) >= max_teams:
                break
        except Exception:
            continue

    return table_top


def build_fan_team_context(favorite_team: Optional[str], table_top: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not favorite_team:
        return None
    fav_lower = favorite_team.lower()
    for row in table_top:
        team_name = row.get("team", "")
        if team_name and fav_lower in team_name.lower():
            gf = row.get("goals_for") or 0
            ga = row.get("goals_against") or 0
            return {
                "team": team_name,
                "rank": row.get("rank"),
                "points": row.get("points"),
                "goal_diff": gf - ga,
            }
    return None


def fetch_news_headlines(news_url: str, max_items: int = 5) -> List[Dict[str, Any]]:
    try:
        resp = requests.get(news_url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to fetch news %s: %s", news_url, exc)
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    headlines: List[Dict[str, Any]] = []
    seen_titles: set[str] = set()
    source_label = urlparse(news_url).netloc.replace("www.", "") or "source"

    def add_headline(title: str, href: str) -> None:
        normalized = clean_headline_text(title)
        if not normalized or len(normalized) < 6:
            return
        key = normalized.lower()
        if key in seen_titles:
            return
        seen_titles.add(key)
        absolute_url = urljoin(news_url, href)
        headlines.append(
            {
                "title": normalized,
                "summary": None,
                "source": source_label,
                "url": absolute_url,
                "published_at": None,
            }
        )

    selectors = [
        ".gs-c-promo-heading",
        "a[href*='/sport/'] h3",
        "article h3",
        "article h2",
    ]
    for selector in selectors:
        for element in soup.select(selector):
            if element.name == "a":
                title = element.get_text(" ", strip=True)
                href = element.get("href")
            else:
                title = element.get_text(" ", strip=True)
                parent = element.find_parent("a", href=True)
                href = parent.get("href") if parent else None
            if not href:
                continue
            add_headline(title, href)
            if len(headlines) >= max_items:
                return headlines

    return headlines[:max_items]


def build_user_league_facts(user: User, db: Session) -> Dict[str, Any]:
    subscriptions = (
        db.query(Subscription)
        .filter(Subscription.user_id == user.id, Subscription.is_active.is_(True))
        .all()
    )
    leagues: List[Dict[str, Any]] = []
    all_sources: List[str] = []
    favorite_team = (user.favorite_team or "").strip()

    for sub in subscriptions:
        config = LEAGUES.get((sub.league_code or "").upper())
        if not config:
            continue
        table_top = fetch_table_top(config["table_url"])
        news_headlines = fetch_news_headlines(config["news_url"])
        seen_titles = {item["title"].lower() for item in news_headlines}
        for extra_url in config.get("extra_news_urls", []):
            extra_headlines = fetch_news_headlines(extra_url)
            for headline in extra_headlines:
                key = (headline.get("title") or "").lower()
                if not key or key in seen_titles:
                    continue
                news_headlines.append(headline)
                seen_titles.add(key)
                if len(news_headlines) >= 5:
                    break
            if len(news_headlines) >= 5:
                break
        news_headlines = news_headlines[:5]
        fan_context = build_fan_team_context(user.favorite_team, table_top)
        fan_team_news: List[Dict[str, Any]] = []
        if favorite_team:
            query = f"{favorite_team} {config['name']} football news"
            fan_team_news = search_team_news(query, max_items=3)
        sources_used = [config["table_url"], config["news_url"], *config.get("extra_news_urls", [])]
        sources_used.extend(item.get("url") for item in fan_team_news if item.get("url"))
        all_sources.extend(sources_used)

        leagues.append(
            {
                "league_code": config["code"],
                "league_name": config["name"],
                "facts": {
                    "league_code": config["code"],
                    "league_name": config["name"],
                    "table_top": table_top,
                    "fan_team_context": fan_context,
                    "upcoming_matches": [],
                    "top_scorers": [],
                    "news_headlines": news_headlines,
                    "fan_team_news": fan_team_news,
                    "sources_used": sources_used,
                },
            }
        )

    unique_sources: List[str] = []
    for src in all_sources:
        if src not in unique_sources:
            unique_sources.append(src)

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
        "sources_used": unique_sources,
    }
