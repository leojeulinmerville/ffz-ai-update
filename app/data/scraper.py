import asyncio
import copy
import os
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
from zoneinfo import ZoneInfo

import httpx
from bs4 import BeautifulSoup

from app.data import football_provider

CACHE_TTL = timedelta(hours=2)
PARIS_TZ = ZoneInfo("Europe/Paris")
HTTP_TIMEOUT = football_provider.DEFAULT_TIMEOUT
USER_AGENT = os.getenv(
    "SCRAPER_USER_AGENT",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/129.0 Safari/537.36",
)
SCRAPE_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "application/json, text/html;q=0.9",
}
LEAGUE_SOURCES: Dict[str, Dict[str, str]] = {
    "PL": {"espn_code": "eng.1", "league_name": "Premier League"},
    "ENG1": {"espn_code": "eng.1", "league_name": "Premier League"},
    "FL1": {"espn_code": "fra.1", "league_name": "Ligue 1"},
    "FRA1": {"espn_code": "fra.1", "league_name": "Ligue 1"},
    "SA": {"espn_code": "ita.1", "league_name": "Serie A"},
    "ITA1": {"espn_code": "ita.1", "league_name": "Serie A"},
    "BL1": {"espn_code": "ger.1", "league_name": "Bundesliga"},
    "GER1": {"espn_code": "ger.1", "league_name": "Bundesliga"},
    "PD": {"espn_code": "esp.1", "league_name": "LaLiga"},
    "ESP1": {"espn_code": "esp.1", "league_name": "LaLiga"},
    "SPA1": {"espn_code": "esp.1", "league_name": "LaLiga"},
    "CL": {"espn_code": "uefa.champions", "league_name": "UEFA Champions League"},
    "UCL": {"espn_code": "uefa.champions", "league_name": "UEFA Champions League"},
}
STANDINGS_URL = "https://site.api.espn.com/apis/v2/sports/soccer/{code}/standings"
SCOREBOARD_URL = "https://site.api.espn.com/apis/site/v2/sports/soccer/{code}/scoreboard"
SCORERS_URL = "https://www.espn.com/soccer/stats/_/league/{code}"

_FACT_CACHE: Dict[str, Dict[str, Any]] = {}
_FACT_LOCK: Optional[asyncio.Lock] = None


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


async def _get_fact_lock() -> asyncio.Lock:
    global _FACT_LOCK
    if _FACT_LOCK is None:
        _FACT_LOCK = asyncio.Lock()
    return _FACT_LOCK


def _cache_key(league_code: str) -> str:
    return f"{league_code.upper()}:{date.today().isoformat()}"


def _parse_utc_datetime(raw: Optional[str]) -> Optional[datetime]:
    if not raw:
        return None
    normalized = raw.strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    if "+" not in normalized[-6:] and normalized[-1].isdigit():
        normalized = f"{normalized}+00:00"
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _paris_iso(raw: Optional[str]) -> Optional[str]:
    dt = _parse_utc_datetime(raw)
    if not dt:
        return None
    return dt.astimezone(PARIS_TZ).isoformat()


async def get_league_facts(league_code: str, fan_team: Optional[str]) -> Dict[str, Any]:
    """
    Aggregate league facts (standings, scorers, fixtures, calendar notes) with a 2h cache.
    """
    normalized = league_code.upper()
    key = _cache_key(normalized)

    lock = await _get_fact_lock()
    async with lock:
        cached = _FACT_CACHE.get(key)
        if cached and _utcnow() - cached["fetched_at"] < CACHE_TTL:
            base_payload = copy.deepcopy(cached["data"])
        else:
            base_payload = await _build_base_payload(normalized)
            _FACT_CACHE[key] = {
                "data": copy.deepcopy(base_payload),
                "fetched_at": _utcnow(),
            }
            stale_keys = [
                bucket_key
                for bucket_key in list(_FACT_CACHE.keys())
                if bucket_key.startswith(f"{normalized}:") and bucket_key != key
            ]
            for bucket_key in stale_keys:
                _FACT_CACHE.pop(bucket_key, None)

    return _attach_fan_context(base_payload, normalized, fan_team)


async def _build_base_payload(league_code: str) -> Dict[str, Any]:
    live_payload = await _build_live_payload(league_code)
    if live_payload:
        return live_payload
    return await _build_provider_payload(league_code)


async def _build_live_payload(league_code: str) -> Optional[Dict[str, Any]]:
    meta = _get_league_meta(league_code)
    if not meta:
        return None

    standings = await _fetch_espn_standings(meta)
    if not standings:
        return None

    table = standings["table"]
    teams = standings["teams"]
    team_lookup = _build_team_lookup(teams)

    top5 = [
        {"club": row.get("team"), "points": row.get("points")}
        for row in table[:5]
        if row.get("team") and row.get("points") is not None
    ]
    tight_gaps = _compute_tight_gaps(top5)

    scorers_task = asyncio.create_task(_fetch_top_scorers(meta))
    scheduled_task = asyncio.create_task(_fetch_scoreboard_matches(meta, future=True, span_days=7))
    finished_task = asyncio.create_task(_fetch_scoreboard_matches(meta, future=False, span_days=30))

    top_scorers_raw, scheduled_matches, finished_matches = await asyncio.gather(
        scorers_task, scheduled_task, finished_task
    )
    top_scorers = _sanitize_top_scorers(top_scorers_raw, team_lookup)
    if not top_scorers:
        top_scorers = football_provider.get_mock_top_scorers(league_code)

    top5_ids = _top_team_ids(top5, team_lookup)
    top5_duels = _compute_top5_duels(top5_ids, scheduled_matches, team_lookup)
    calendar_notes = _compute_calendar_notes(top5_ids, scheduled_matches, team_lookup)

    timestamp_iso = _utcnow().isoformat()
    return {
        "league_code": league_code,
        "league_name": standings["league_name"],
        "season_current": True,
        "top5": top5,
        "top_scorers": top_scorers,
        "tight_gaps": tight_gaps,
        "top5_duels_this_week": top5_duels,
        "calendar_notes": calendar_notes,
        "source_timestamps": {
            "standings": timestamp_iso,
            "scorers": timestamp_iso,
            "fixtures": timestamp_iso,
            "results": timestamp_iso,
        },
        "teams": teams,
        "matches_scheduled": scheduled_matches,
        "matches_finished": finished_matches,
    }


async def _build_provider_payload(league_code: str) -> Dict[str, Any]:
    league_data = await football_provider.get_league_context(league_code)
    league_name = league_data.get("league_name") or league_code
    table = league_data.get("table") or []
    teams = league_data.get("teams") or []
    team_lookup = _build_team_lookup(teams)

    top5 = [
        {"club": row.get("team"), "points": row.get("points")}
        for row in table[:5]
        if row.get("team") and row.get("points") is not None
    ]

    top_scorers = _sanitize_top_scorers(league_data.get("top_scorers") or [], team_lookup)
    if not top_scorers:
        top_scorers = football_provider.get_mock_top_scorers(league_code)
    tight_gaps = _compute_tight_gaps(top5)

    scheduled_matches = league_data.get("matches_scheduled") or []
    finished_matches = league_data.get("matches_finished") or []

    top5_ids = _top_team_ids(top5, team_lookup)
    top5_duels = _compute_top5_duels(top5_ids, scheduled_matches, team_lookup)
    calendar_notes = _compute_calendar_notes(top5_ids, scheduled_matches, team_lookup)

    timestamp_iso = _utcnow().isoformat()
    source_timestamps = {
        "standings": timestamp_iso,
        "scorers": timestamp_iso,
        "fixtures": timestamp_iso,
        "results": timestamp_iso,
    }

    return {
        "league_code": league_code,
        "league_name": league_name,
        "season_current": bool(table),
        "top5": top5,
        "top_scorers": top_scorers,
        "tight_gaps": tight_gaps,
        "top5_duels_this_week": top5_duels,
        "calendar_notes": calendar_notes,
        "source_timestamps": source_timestamps,
        "teams": teams,
        "matches_scheduled": scheduled_matches,
        "matches_finished": finished_matches,
    }


async def _fetch_espn_standings(meta: Dict[str, str]) -> Optional[Dict[str, Any]]:
    url = STANDINGS_URL.format(code=meta["espn_code"])
    payload = await _http_get_json(url)
    if not payload:
        return None

    children = payload.get("children") or []
    standings_block = next(
        (child for child in children if child.get("standings", {}).get("entries")), None
    )
    if not standings_block:
        return None

    entries = standings_block.get("standings", {}).get("entries", [])
    table: List[Dict[str, Any]] = []
    teams: List[Dict[str, Any]] = []
    seen_team_ids: set = set()

    for idx, entry in enumerate(entries, start=1):
        team = entry.get("team") or {}
        display_name = team.get("displayName") or team.get("shortDisplayName")
        points = _extract_stat_value(entry.get("stats", []), "points")
        if display_name is None or points is None:
            continue
        team_id = _normalize_team_id(team.get("id"))
        table.append(
            {
                "rank": idx,
                "team": display_name,
                "points": int(points),
                "team_id": team_id,
            }
        )
        if team_id not in seen_team_ids:
            teams.append(
                {
                    "id": team_id,
                    "name": display_name,
                    "shortName": team.get("shortDisplayName") or team.get("abbreviation"),
                    "tla": team.get("abbreviation"),
                }
            )
            seen_team_ids.add(team_id)

    return {
        "league_name": standings_block.get("name") or meta["league_name"],
        "table": table,
        "teams": teams,
    }


async def _fetch_top_scorers(meta: Dict[str, str]) -> List[Dict[str, Any]]:
    url = SCORERS_URL.format(code=meta["espn_code"])
    html = await _http_get_html(url)
    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")
    if not table:
        return []

    scorers: List[Dict[str, Any]] = []
    for row in table.find_all("tr")[1:]:
        cells = row.find_all("td")
        if len(cells) < 4:
            continue
        player = cells[1].text.strip()
        club = cells[2].text.strip()
        goals = _safe_int(cells[3].text.strip())
        if player and club and goals is not None:
            scorers.append({"player": player, "club": club, "goals": goals})
        if len(scorers) == 5:
            break
    return scorers


async def _fetch_scoreboard_matches(
    meta: Dict[str, str],
    *,
    future: bool,
    span_days: int,
) -> List[Dict[str, Any]]:
    if span_days <= 0:
        return []

    today = _utcnow().date()
    if future:
        start = today
        end = today + timedelta(days=span_days)
    else:
        start = today - timedelta(days=span_days)
        end = today

    if start > end:
        start, end = end, start

    date_range = f"{start:%Y%m%d}-{end:%Y%m%d}"
    url = SCOREBOARD_URL.format(code=meta["espn_code"])
    payload = await _http_get_json(url, params={"dates": date_range})
    if not payload:
        return []

    events = payload.get("events") or []
    normalized = [_normalize_event(event) for event in events]
    if future:
        return [event for event in normalized if not event.get("is_final")]
    return [event for event in normalized if event.get("is_final")]


def _normalize_event(event: Dict[str, Any]) -> Dict[str, Any]:
    competitions = event.get("competitions") or [{}]
    comp = competitions[0]
    competitors = comp.get("competitors") or []

    home = next((item for item in competitors if item.get("homeAway") == "home"), None)
    away = next((item for item in competitors if item.get("homeAway") == "away"), None)

    def _team_payload(node: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        team_info = (node or {}).get("team") or {}
        team_id = _normalize_team_id(team_info.get("id"))
        return {
            "id": team_id,
            "name": team_info.get("displayName") or team_info.get("name"),
        }

    return {
        "utcDate": event.get("date"),
        "homeTeam": _team_payload(home),
        "awayTeam": _team_payload(away),
        "score": {
            "home": _safe_int((home or {}).get("score")),
            "away": _safe_int((away or {}).get("score")),
        },
        "status": comp.get("status"),
        "is_final": bool(comp.get("status", {}).get("type", {}).get("completed")),
    }


def _extract_stat_value(stats: List[Dict[str, Any]], name: str) -> Optional[int]:
    for stat in stats or []:
        if stat.get("name") == name and stat.get("value") is not None:
            try:
                return int(stat["value"])
            except (TypeError, ValueError):
                return None
    return None


def _attach_fan_context(base_payload: Dict[str, Any], league_code: str, fan_team: Optional[str]) -> Dict[str, Any]:
    payload = copy.deepcopy(base_payload)
    teams = payload.pop("teams", [])
    scheduled = payload.pop("matches_scheduled", [])
    finished = payload.pop("matches_finished", [])

    fan_team_canonical, team_id = _resolve_fan_team(fan_team, teams)
    fan_form = _compute_fan_form(team_id, finished)
    next_match = _compute_next_match(team_id, scheduled)

    payload.update(
        {
            "fan_team": fan_team_canonical,
            "fan_form": fan_form,
            "next_match": next_match,
        }
    )
    return payload


def _build_team_lookup(teams: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    lookup: Dict[str, Dict[str, Any]] = {}
    for team in teams:
        team["id"] = _normalize_team_id(team.get("id"))
        for key in filter(
            None,
            [
                team.get("name"),
                team.get("shortName"),
                team.get("tla"),
            ],
        ):
            lookup[key.strip().casefold()] = team
    return lookup


def _sanitize_top_scorers(
    scorers: List[Dict[str, Any]],
    team_lookup: Dict[str, Dict[str, Any]],
) -> List[Dict[str, Any]]:
    clean: List[Dict[str, Any]] = []
    for scorer in scorers:
        name = scorer.get("player") or scorer.get("name")
        club = scorer.get("team")
        goals = scorer.get("goals")
        if not (name and club and goals is not None):
            continue
        if club.strip().casefold() not in team_lookup:
            continue
        clean.append({"player": name, "club": club, "goals": goals})
        if len(clean) == 3:
            break
    return clean


def _compute_tight_gaps(top5: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    gaps: List[Dict[str, Any]] = []
    for idx in range(len(top5) - 1):
        current = top5[idx]
        nxt = top5[idx + 1]
        try:
            diff = abs(int(current["points"]) - int(nxt["points"]))
        except (TypeError, ValueError):
            continue
        if diff <= 2:
            gaps.append(
                {
                    "pos1": idx + 1,
                    "pos2": idx + 2,
                    "gap_points": diff,
                }
            )
    return gaps


def _top_team_ids(top5: List[Dict[str, Any]], team_lookup: Dict[str, Dict[str, Any]]) -> List[int]:
    ids: List[int] = []
    for entry in top5:
        team = entry.get("club")
        if not team:
            continue
        record = team_lookup.get(team.strip().casefold())
        normalized_id = _normalize_team_id((record or {}).get("id"))
        if normalized_id is not None:
            ids.append(normalized_id)
    return ids


def _compute_top5_duels(
    top_ids: List[int],
    scheduled_matches: List[Dict[str, Any]],
    team_lookup: Dict[str, Dict[str, Any]],
) -> List[Dict[str, Any]]:
    duels: List[Dict[str, Any]] = []
    if not top_ids:
        return duels

    top_set = {_normalize_team_id(team_id) for team_id in top_ids}
    for match in scheduled_matches:
        home = _normalize_team_id((match.get("homeTeam") or {}).get("id"))
        away = _normalize_team_id((match.get("awayTeam") or {}).get("id"))
        if home in top_set and away in top_set:
            utc_iso = match.get("utcDate")
            duels.append(
                {
                    "home": (match.get("homeTeam") or {}).get("name"),
                    "away": (match.get("awayTeam") or {}).get("name"),
                    "date_utc": utc_iso,
                    "date_paris": _paris_iso(utc_iso),
                }
            )
    return duels[:5]


def _compute_calendar_notes(
    top_ids: List[int],
    scheduled_matches: List[Dict[str, Any]],
    team_lookup: Dict[str, Dict[str, Any]],
) -> List[Dict[str, Any]]:
    notes: List[Dict[str, Any]] = []
    if not top_ids:
        return notes

    horizon = _utcnow() + timedelta(days=7)
    counts: Dict[Any, int] = {team_id: 0 for team_id in top_ids}

    for match in scheduled_matches:
        kickoff = _parse_utc_datetime(match.get("utcDate"))
        if kickoff is None or kickoff > horizon:
            continue
        for side in ("homeTeam", "awayTeam"):
            side_id = _normalize_team_id((match.get(side) or {}).get("id"))
            if side_id in counts:
                counts[side_id] += 1

    for team_id, qty in counts.items():
        if qty >= 3:
            team_name = _team_name_from_id(team_id, team_lookup)
            if team_name:
                notes.append({"team": team_name, "matches": qty})
    return notes[:5]


def _team_name_from_id(team_id: Any, team_lookup: Dict[str, Dict[str, Any]]) -> Optional[str]:
    target = _normalize_team_id(team_id)
    for record in team_lookup.values():
        if _normalize_team_id(record.get("id")) == target:
            return record.get("name")
    return None


def _resolve_fan_team(fan_team: Optional[str], teams: List[Dict[str, Any]]) -> Tuple[Optional[str], Optional[int]]:
    if not fan_team:
        return None, None
    needle = fan_team.strip().casefold()
    for team in teams:
        candidates = [
            team.get("name"),
            team.get("shortName"),
            team.get("tla"),
        ]
        for candidate in candidates:
            if candidate and candidate.strip().casefold() == needle:
                return team.get("name") or candidate, _normalize_team_id(team.get("id"))
    return None, None


def _compute_fan_form(team_id: Optional[int], finished_matches: List[Dict[str, Any]]) -> List[str]:
    if team_id is None:
        return []
    target = _normalize_team_id(team_id)
    relevant = []
    for match in finished_matches:
        home = _normalize_team_id((match.get("homeTeam") or {}).get("id"))
        away = _normalize_team_id((match.get("awayTeam") or {}).get("id"))
        if target not in (home, away):
            continue
        score_block = match.get("score") or {}
        if "fullTime" in score_block:
            score_block = score_block.get("fullTime") or {}
        home_goals = _safe_int(score_block.get("home"))
        away_goals = _safe_int(score_block.get("away"))
        if home_goals is None or away_goals is None:
            continue
        if home_goals == away_goals:
            result = "D"
        elif (home_goals > away_goals and home == target) or (away_goals > home_goals and away == target):
            result = "W"
        else:
            result = "L"
        relevant.append((match.get("utcDate"), result))

    relevant.sort(key=lambda item: item[0] or "", reverse=True)
    return [entry[1] for entry in relevant[:5]]


def _compute_next_match(team_id: Optional[int], scheduled_matches: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if team_id is None:
        return None
    target = _normalize_team_id(team_id)
    future_matches = []
    for match in scheduled_matches:
        home = _normalize_team_id((match.get("homeTeam") or {}).get("id"))
        away = _normalize_team_id((match.get("awayTeam") or {}).get("id"))
        if target not in (home, away):
            continue
        utc_date = match.get("utcDate")
        if not utc_date:
            continue
        future_matches.append((utc_date, match))

    if not future_matches:
        return None

    future_matches.sort(key=lambda item: item[0])
    selected = future_matches[0][1]
    utc_iso = selected.get("utcDate")
    return {
        "home": (selected.get("homeTeam") or {}).get("name"),
        "away": (selected.get("awayTeam") or {}).get("name"),
        "utc_kickoff": utc_iso,
        "paris_kickoff": _paris_iso(utc_iso),
    }


def _get_league_meta(league_code: str) -> Optional[Dict[str, str]]:
    normalized = league_code.upper()
    if normalized in LEAGUE_SOURCES:
        return LEAGUE_SOURCES[normalized]
    alias = football_provider.LEAGUE_CODE_ALIASES.get(normalized)
    if alias:
        target = alias.get("api_code", "").upper()
        return LEAGUE_SOURCES.get(target)
    return None


def _normalize_team_id(raw: Any) -> Optional[Any]:
    if raw is None:
        return None
    if isinstance(raw, int):
        return raw
    try:
        return int(str(raw))
    except (TypeError, ValueError):
        try:
            return str(raw).strip()
        except Exception:
            return None


def _safe_int(value: Any) -> Optional[int]:
    if value is None:
        return None
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


async def _http_get_json(url: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT, headers=SCRAPE_HEADERS) as client:
            response = await client.get(url, params=params)
    except httpx.HTTPError:
        return None
    if response.status_code != 200:
        return None
    try:
        return response.json()
    except ValueError:
        return None


async def _http_get_html(url: str) -> Optional[str]:
    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT, headers=SCRAPE_HEADERS) as client:
            response = await client.get(url)
    except httpx.HTTPError:
        return None
    if response.status_code != 200:
        return None
    return response.text
