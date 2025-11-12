import asyncio
import copy
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import httpx

API_BASE_URL = "https://api.football-data.org/v4"
API_KEY = os.getenv("FOOTBALL_DATA_API_KEY")
DEFAULT_TIMEOUT = 10.0
CACHE_TTL = timedelta(hours=2)

# Mapping between internal codes and football-data.org competitions.
SUPPORTED_LEAGUES: List[Dict[str, str]] = [
    {"code": "PL", "name": "Premier League", "country": "England"},
    {"code": "FL1", "name": "Ligue 1", "country": "France"},
    {"code": "PD", "name": "LaLiga", "country": "Spain"},
    {"code": "BL1", "name": "Bundesliga", "country": "Germany"},
    {"code": "SA", "name": "Serie A", "country": "Italy"},
    {"code": "CL", "name": "UEFA Champions League", "country": "Europe"},
]

LEAGUE_CODE_ALIASES: Dict[str, Dict[str, str]] = {
    "FRA1": {"api_code": "FL1", "name": "Ligue 1"},
    "ENG1": {"api_code": "PL", "name": "Premier League"},
    "ITA1": {"api_code": "SA", "name": "Serie A"},
    "GER1": {"api_code": "BL1", "name": "Bundesliga"},
    "ESP1": {"api_code": "PD", "name": "LaLiga"},
    "SPA1": {"api_code": "PD", "name": "LaLiga"},
    "CL": {"api_code": "CL", "name": "Champions League"},
    "UCL": {"api_code": "CL", "name": "Champions League"},
}

MOCK_LEAGUES: Dict[str, Dict[str, Any]] = {
    "FL1": {
        "league_code": "FL1",
        "league_name": "Ligue 1",
        "table": [
            {"rank": 1, "team": "Paris SG", "points": 27},
            {"rank": 2, "team": "AS Monaco", "points": 25},
            {"rank": 3, "team": "OGC Nice", "points": 24},
            {"rank": 4, "team": "Olympique Lyonnais", "points": 21},
            {"rank": 5, "team": "Lille", "points": 20},
        ],
    },
    "PL": {
        "league_code": "PL",
        "league_name": "Premier League",
        "table": [
            {"rank": 1, "team": "Manchester City", "points": 30},
            {"rank": 2, "team": "Liverpool", "points": 28},
            {"rank": 3, "team": "Arsenal", "points": 26},
            {"rank": 4, "team": "Tottenham Hotspur", "points": 24},
            {"rank": 5, "team": "Aston Villa", "points": 22},
        ],
    },
    "PD": {
        "league_code": "PD",
        "league_name": "LaLiga",
        "table": [
            {"rank": 1, "team": "Real Madrid", "points": 30},
            {"rank": 2, "team": "FC Barcelona", "points": 28},
            {"rank": 3, "team": "Atlético Madrid", "points": 27},
            {"rank": 4, "team": "Real Sociedad", "points": 24},
            {"rank": 5, "team": "Athletic Club", "points": 22},
        ],
    },
    "BL1": {
        "league_code": "BL1",
        "league_name": "Bundesliga",
        "table": [
            {"rank": 1, "team": "FC Bayern München", "points": 29},
            {"rank": 2, "team": "Bayer 04 Leverkusen", "points": 28},
            {"rank": 3, "team": "Borussia Dortmund", "points": 25},
            {"rank": 4, "team": "RB Leipzig", "points": 23},
            {"rank": 5, "team": "VfB Stuttgart", "points": 21},
        ],
    },
    "SA": {
        "league_code": "SA",
        "league_name": "Serie A",
        "table": [
            {"rank": 1, "team": "Inter", "points": 29},
            {"rank": 2, "team": "Juventus", "points": 27},
            {"rank": 3, "team": "Milan", "points": 26},
            {"rank": 4, "team": "Napoli", "points": 23},
            {"rank": 5, "team": "Roma", "points": 20},
        ],
    },
    "CL": {
        "league_code": "CL",
        "league_name": "Champions League",
        "table": [
            {"rank": 1, "team": "Manchester City", "points": 12},
            {"rank": 2, "team": "Real Madrid", "points": 12},
            {"rank": 3, "team": "Bayern München", "points": 11},
            {"rank": 4, "team": "Barcelona", "points": 10},
            {"rank": 5, "team": "Paris SG", "points": 9},
        ],
    },
}

MOCK_TOP_SCORERS: Dict[str, List[Dict[str, Any]]] = {
    "FL1": [
        {"player": "Kylian Mbappé", "team": "Paris SG", "goals": 9},
        {"player": "Wissam Ben Yedder", "team": "AS Monaco", "goals": 7},
        {"player": "Jonathan David", "team": "LOSC Lille", "goals": 6},
    ],
    "PL": [
        {"player": "Erling Haaland", "team": "Manchester City", "goals": 11},
        {"player": "Mohamed Salah", "team": "Liverpool", "goals": 8},
        {"player": "Bukayo Saka", "team": "Arsenal", "goals": 6},
    ],
    "PD": [
        {"player": "Vinícius Júnior", "team": "Real Madrid", "goals": 10},
        {"player": "Robert Lewandowski", "team": "FC Barcelona", "goals": 9},
        {"player": "Álvaro Morata", "team": "Atlético Madrid", "goals": 8},
    ],
    "BL1": [
        {"player": "Harry Kane", "team": "FC Bayern München", "goals": 12},
        {"player": "Serhou Guirassy", "team": "VfB Stuttgart", "goals": 9},
        {"player": "Donyell Malen", "team": "Borussia Dortmund", "goals": 7},
    ],
    "SA": [
        {"player": "Lautaro Martínez", "team": "Inter", "goals": 11},
        {"player": "Victor Osimhen", "team": "Napoli", "goals": 8},
        {"player": "Paulo Dybala", "team": "Roma", "goals": 6},
    ],
    "CL": [
        {"player": "Julián Álvarez", "team": "Manchester City", "goals": 5},
        {"player": "Jude Bellingham", "team": "Real Madrid", "goals": 4},
        {"player": "Leroy Sané", "team": "FC Bayern München", "goals": 4},
    ],
}

MOCK_LEAGUE_TEAM_LIST: Dict[str, List[Dict[str, Any]]] = {
    "FL1": [
        {"id": 524, "name": "Paris SG", "short_name": "Paris SG", "tla": "PSG"},
        {"id": 529, "name": "AS Monaco", "short_name": "Monaco", "tla": "ASM"},
        {"id": 541, "name": "Olympique Lyonnais", "short_name": "Lyon", "tla": "OL"},
        {"id": 548, "name": "Olympique de Marseille", "short_name": "Marseille", "tla": "OM"},
        {"id": 532, "name": "OGC Nice", "short_name": "Nice", "tla": "NCE"},
    ],
    "PL": [
        {"id": 65, "name": "Manchester City", "short_name": "Man City", "tla": "MCI"},
        {"id": 64, "name": "Liverpool", "short_name": "Liverpool", "tla": "LIV"},
        {"id": 57, "name": "Arsenal", "short_name": "Arsenal", "tla": "ARS"},
        {"id": 61, "name": "Chelsea", "short_name": "Chelsea", "tla": "CHE"},
        {"id": 66, "name": "Manchester United", "short_name": "Man United", "tla": "MUN"},
    ],
}

MOCK_TEAMS: Dict[Tuple[str, str], Dict[str, Any]] = {
    ("FL1", "paris sg"): {
        "team_name": "Paris SG",
        "recent_matches": [
            {"opponent": "AS Monaco", "score": "3-1", "result": "W", "scorers": ["Mbappe (2)", "Dembele"], "utc_date": "2025-10-12T19:00:00Z"},
            {"opponent": "Nice", "score": "1-1", "result": "D", "scorers": ["Mbappe"], "utc_date": "2025-10-05T19:00:00Z"},
            {"opponent": "Lyon", "score": "2-0", "result": "W", "scorers": ["Asensio", "Vitinha"], "utc_date": "2025-09-28T19:00:00Z"},
        ],
        "next_match": {
            "opponent": "Lyon",
            "kickoff_utc": "2025-11-02T20:45:00Z",
            "home": True,
        },
        "key_players": [
            {"name": "Kylian Mbappe", "note": "4 goals in last 5 games"},
            {"name": "Ousmane Dembele", "note": "2 assists last match"},
        ],
    },
    ("PL", "arsenal"): {
        "team_name": "Arsenal",
        "recent_matches": [
            {"opponent": "Manchester City", "score": "2-1", "result": "W", "scorers": ["Saka", "Odegaard"], "utc_date": "2025-10-11T16:30:00Z"},
            {"opponent": "Chelsea", "score": "1-1", "result": "D", "scorers": ["Martinelli"], "utc_date": "2025-10-05T13:00:00Z"},
            {"opponent": "Tottenham Hotspur", "score": "0-1", "result": "L", "scorers": [], "utc_date": "2025-09-29T15:30:00Z"},
        ],
        "next_match": {
            "opponent": "Aston Villa",
            "kickoff_utc": "2025-11-03T17:30:00Z",
            "home": False,
        },
        "key_players": [
            {"name": "Bukayo Saka", "note": "Decisive in the last derby"},
            {"name": "Martin Odegaard", "note": "3 assists in 4 matches"},
        ],
    },
}

_league_cache: Dict[Tuple[str, str], Dict[str, Any]] = {}
_team_cache: Dict[Tuple[str, str, str], Dict[str, Any]] = {}
_league_lock: Optional[asyncio.Lock] = None
_team_lock: Optional[asyncio.Lock] = None


def _utcnow() -> datetime:
    return datetime.utcnow()


def _current_bucket() -> str:
    return _utcnow().date().isoformat()


def list_supported_leagues() -> List[Dict[str, str]]:
    return copy.deepcopy(SUPPORTED_LEAGUES)


def get_mock_top_scorers(league_code: str) -> List[Dict[str, Any]]:
    code = league_code.upper()
    return copy.deepcopy(
        MOCK_TOP_SCORERS.get(code) or MOCK_TOP_SCORERS.get(LEAGUE_CODE_ALIASES.get(code, {}).get("api_code", ""))
        or []
    )


async def _get_league_lock() -> asyncio.Lock:
    global _league_lock
    if _league_lock is None:
        _league_lock = asyncio.Lock()
    return _league_lock


async def _get_team_lock() -> asyncio.Lock:
    global _team_lock
    if _team_lock is None:
        _team_lock = asyncio.Lock()
    return _team_lock


async def get_league_context(league_code: str) -> Dict[str, Any]:
    """
    Return structured league data (standings, teams, top scorers) with caching.
    """
    normalized_code = league_code.upper()
    bucket = _current_bucket()
    cache_key = (normalized_code, bucket)

    lock = await _get_league_lock()
    async with lock:
        cached = _league_cache.get(cache_key)
        if cached and _utcnow() - cached["fetched_at"] < CACHE_TTL:
            return copy.deepcopy(cached["data"])

    fresh = await _fetch_league_context(normalized_code)

    lock = await _get_league_lock()
    async with lock:
        _league_cache[cache_key] = {
            "data": copy.deepcopy(fresh),
            "fetched_at": _utcnow(),
        }
        stale_keys = [
            key for key in list(_league_cache.keys()) if key[0] == normalized_code and key != cache_key
        ]
        for key in stale_keys:
            _league_cache.pop(key, None)

    return copy.deepcopy(fresh)


async def get_team_context(team_name: Optional[str], league_code: str) -> Optional[Dict[str, Any]]:
    """
    Return contextual information (recent form, next match, key players) for a team.
    """
    if not team_name:
        return None

    normalized_league = league_code.upper()
    normalized_team = team_name.strip().casefold()
    bucket = _current_bucket()
    cache_key = (normalized_league, normalized_team, bucket)

    lock = await _get_team_lock()
    async with lock:
        cached = _team_cache.get(cache_key)
        if cached and _utcnow() - cached["fetched_at"] < CACHE_TTL:
            return copy.deepcopy(cached["data"])

    fresh = await _fetch_team_context(normalized_league, normalized_team)
    if fresh is None:
        return None

    lock = await _get_team_lock()
    async with lock:
        _team_cache[cache_key] = {
            "data": copy.deepcopy(fresh),
            "fetched_at": _utcnow(),
        }
        stale_keys = [
            key
            for key in list(_team_cache.keys())
            if key[0] == normalized_league and key[1] == normalized_team and key != cache_key
        ]
        for key in stale_keys:
            _team_cache.pop(key, None)

    return copy.deepcopy(fresh)


async def _fetch_league_context(league_code: str) -> Dict[str, Any]:
    api_code, friendly_name = _resolve_league_meta(league_code)

    standings_data = await _request(f"/competitions/{api_code}/standings")
    teams_data = await _request(f"/competitions/{api_code}/teams")
    scorers_data = await _request(
        f"/competitions/{api_code}/scorers", params={"limit": 30}
    )

    if not standings_data:
        return _mock_league_payload(league_code, api_code, friendly_name)

    league_name = (
        friendly_name
        or (standings_data.get("competition") or {}).get("name")
        or standings_data.get("area", {}).get("name")
        or league_code
    )

    table = _extract_table_rows(standings_data)
    teams = _extract_team_list(teams_data)
    top_scorers = _extract_top_scorers(scorers_data)

    if not teams:
        teams = _mock_league_team_list(league_code, api_code)
    if not top_scorers:
        top_scorers = MOCK_TOP_SCORERS.get(api_code) or MOCK_TOP_SCORERS.get(league_code) or []

    return {
        "league_code": league_code,
        "league_name": league_name,
        "table": table,
        "teams": teams,
        "top_scorers": top_scorers,
        "fetched_from_live": bool(API_KEY),
    }


async def _fetch_team_context(league_code: str, normalized_team: str) -> Optional[Dict[str, Any]]:
    api_code, _ = _resolve_league_meta(league_code)
    league_data = await get_league_context(league_code)
    teams = league_data.get("teams") or []

    team_record = _match_team(teams, normalized_team)
    mock_payload = _mock_team_payload(normalized_team, league_code, api_code)

    if not team_record:
        return mock_payload

    team_id = team_record.get("id")
    canonical_name = team_record.get("name") or mock_payload.get("team_name") if mock_payload else None

    recent_matches = await _fetch_recent_matches(team_id) if team_id else []
    next_match = await _fetch_next_match(team_id) if team_id else None
    key_players = _build_key_players(
        league_data.get("top_scorers") or [],
        canonical_name or team_record.get("name"),
    )

    if not recent_matches and mock_payload:
        recent_matches = mock_payload.get("recent_matches", [])
    if not next_match and mock_payload:
        next_match = mock_payload.get("next_match")
    if not key_players and mock_payload:
        key_players = mock_payload.get("key_players", [])

    if not (recent_matches or next_match or key_players):
        return mock_payload

    return {
        "team_name": canonical_name or team_record.get("name") or mock_payload.get("team_name"),
        "recent_matches": recent_matches,
        "next_match": next_match,
        "key_players": key_players,
    }


# --------------------------------------------------------------------------- #
# Helper functions
# --------------------------------------------------------------------------- #


async def _request(path: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    if not API_KEY:
        return None

    headers = {"X-Auth-Token": API_KEY}

    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        try:
            response = await client.get(f"{API_BASE_URL}{path}", params=params, headers=headers)
        except httpx.HTTPError:
            return None

    if response.status_code != 200:
        return None

    try:
        return response.json()
    except ValueError:
        return None


def _resolve_league_meta(league_code: str) -> Tuple[str, Optional[str]]:
    meta = LEAGUE_CODE_ALIASES.get(league_code.upper())
    if meta:
        return meta["api_code"], meta.get("name")
    return league_code.upper(), None


def _mock_league_payload(league_code: str, api_code: str, friendly_name: Optional[str]) -> Dict[str, Any]:
    template = (
        copy.deepcopy(MOCK_LEAGUES.get(league_code))
        or copy.deepcopy(MOCK_LEAGUES.get(api_code))
        or {"league_code": league_code, "league_name": friendly_name or league_code, "table": []}
    )
    template.setdefault("teams", copy.deepcopy(MOCK_LEAGUE_TEAM_LIST.get(league_code)) or copy.deepcopy(MOCK_LEAGUE_TEAM_LIST.get(api_code)) or [])
    template.setdefault("top_scorers", copy.deepcopy(MOCK_TOP_SCORERS.get(api_code)) or copy.deepcopy(MOCK_TOP_SCORERS.get(league_code)) or [])
    template["league_code"] = league_code
    if friendly_name:
        template["league_name"] = friendly_name
    return template


def _mock_team_payload(normalized_team: str, league_code: str, api_code: str) -> Optional[Dict[str, Any]]:
    lookup_keys = [
        (league_code, normalized_team),
        (league_code.upper(), normalized_team),
        (api_code, normalized_team),
    ]
    for key in lookup_keys:
        if key in MOCK_TEAMS:
            return copy.deepcopy(MOCK_TEAMS[key])
    return None


def _mock_league_team_list(league_code: str, api_code: str) -> List[Dict[str, Any]]:
    return copy.deepcopy(MOCK_LEAGUE_TEAM_LIST.get(league_code) or MOCK_LEAGUE_TEAM_LIST.get(api_code) or [])


def _extract_table_rows(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    standings = data.get("standings") or []
    table_section: Optional[List[Dict[str, Any]]] = None

    for block in standings:
        if block.get("type") == "TOTAL":
            table_section = block.get("table") or []
            break
    if table_section is None and standings:
        table_section = standings[0].get("table") or []

    rows: List[Dict[str, Any]] = []
    for row in table_section or []:
        team_info = row.get("team") or {}
        rows.append(
            {
                "rank": row.get("position"),
                "team": team_info.get("name"),
                "points": row.get("points"),
                "played_games": row.get("playedGames"),
                "goal_difference": row.get("goalDifference"),
            }
        )
    return rows


def _extract_team_list(data: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not data:
        return []
    teams: List[Dict[str, Any]] = []
    for team in data.get("teams") or []:
        teams.append(
            {
                "id": team.get("id"),
                "name": team.get("name"),
                "short_name": team.get("shortName"),
                "tla": team.get("tla"),
            }
        )
    return teams


def _extract_top_scorers(data: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not data:
        return []
    results: List[Dict[str, Any]] = []
    for entry in data.get("scorers") or []:
        player = entry.get("player") or {}
        team = entry.get("team") or {}
        results.append(
            {
                "player": player.get("name"),
                "team": team.get("name"),
                "goals": entry.get("goals"),
                "assists": entry.get("assists"),
            }
        )
    return results


def _match_team(teams: List[Dict[str, Any]], normalized_team: str) -> Optional[Dict[str, Any]]:
    for team in teams:
        candidates = [
            (team.get("name") or "").casefold(),
            (team.get("short_name") or "").casefold(),
            (team.get("tla") or "").casefold(),
        ]
        if normalized_team in candidates:
            return team
    return None


async def _fetch_recent_matches(team_id: Optional[int], limit: int = 3) -> List[Dict[str, Any]]:
    if not team_id:
        return []
    data = await _request(
        f"/teams/{team_id}/matches",
        params={"status": "FINISHED", "limit": limit, "order": "desc"},
    )
    if not data:
        return []

    matches: List[Dict[str, Any]] = []
    for match in data.get("matches", [])[:limit]:
        matches.append(_normalize_match(match, team_id))
    return matches


async def _fetch_next_match(team_id: Optional[int]) -> Optional[Dict[str, Any]]:
    if not team_id:
        return None
    data = await _request(
        f"/teams/{team_id}/matches",
        params={"status": "SCHEDULED", "limit": 1, "order": "asc"},
    )
    if not data:
        return None

    matches = data.get("matches") or []
    if not matches:
        return None

    match = matches[0]
    home_team = match.get("homeTeam") or {}
    away_team = match.get("awayTeam") or {}

    return {
        "opponent": away_team.get("name") if home_team.get("id") == team_id else home_team.get("name"),
        "kickoff_utc": match.get("utcDate"),
        "home": home_team.get("id") == team_id,
    }


def _build_key_players(top_scorers: List[Dict[str, Any]], team_name: Optional[str]) -> List[Dict[str, Any]]:
    if not team_name:
        return []

    normalized = team_name.casefold()
    players: List[Dict[str, Any]] = []
    for entry in top_scorers:
        team_entry = entry.get("team")
        if not team_entry:
            continue
        if team_entry.casefold() != normalized:
            continue
        goals = entry.get("goals")
        assists = entry.get("assists")
        note_parts = []
        if goals is not None:
            note_parts.append(f"{goals} goals this season")
        if assists:
            note_parts.append(f"{assists} assists")
        note = ", ".join(note_parts) if note_parts else "Key contributor"
        players.append({"name": entry.get("player"), "note": note})
        if len(players) >= 3:
            break
    return players


def _normalize_match(match: Dict[str, Any], team_id: int) -> Dict[str, Any]:
    home_team = match.get("homeTeam") or {}
    away_team = match.get("awayTeam") or {}
    score = match.get("score") or {}
    full_time = score.get("fullTime") or {}
    home_goals = full_time.get("home")
    away_goals = full_time.get("away")

    result = "D"
    if home_goals is not None and away_goals is not None:
        if home_team.get("id") == team_id:
            if home_goals > away_goals:
                result = "W"
            elif home_goals < away_goals:
                result = "L"
        else:
            if away_goals > home_goals:
                result = "W"
            elif away_goals < home_goals:
                result = "L"

    opponent = away_team.get("name") if home_team.get("id") == team_id else home_team.get("name")
    score_str = (
        f"{home_goals}-{away_goals}"
        if home_goals is not None and away_goals is not None
        else None
    )

    return {
        "opponent": opponent,
        "score": score_str,
        "result": result,
        "scorers": [],
        "utc_date": match.get("utcDate"),
    }
