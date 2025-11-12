from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass(frozen=True)
class LeagueMeta:
    code: str
    name: str
    country: str
    bbc_slug: str


LEAGUE_CATALOG: Dict[str, LeagueMeta] = {
    "PL": LeagueMeta("PL", "Premier League", "England", "premier-league"),
    "FL1": LeagueMeta("FL1", "Ligue 1", "France", "french-ligue-one"),
    "PD": LeagueMeta("PD", "LaLiga", "Spain", "spanish-la-liga"),
    "BL1": LeagueMeta("BL1", "Bundesliga", "Germany", "german-bundesliga"),
    "SA": LeagueMeta("SA", "Serie A", "Italy", "italian-serie-a"),
    "CL": LeagueMeta("CL", "UEFA Champions League", "Europe", "champions-league"),
}


def list_leagues() -> List[Dict[str, str]]:
    return [
        {
            "code": meta.code,
            "name": meta.name,
            "country": meta.country,
        }
        for meta in LEAGUE_CATALOG.values()
    ]


def get_league_meta(code: str) -> Optional[LeagueMeta]:
    return LEAGUE_CATALOG.get(code.upper())
