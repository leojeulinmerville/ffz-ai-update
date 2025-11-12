from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List

from app.data.extractor.leagues import FixtureRow, LeagueBundle, StandingRow


@dataclass
class NormalizedFacts:
    facts: List[Dict]
    payload: Dict
    sources: List[str]


def bundle_to_facts(bundle: LeagueBundle) -> NormalizedFacts:
    facts: List[Dict] = []
    source_url = f"https://www.bbc.com/sport/football/{bundle.meta.bbc_slug}"
    sources = [source_url + suffix for suffix in ("/table", "/scores-fixtures", "/top-scorers")]

    for row in bundle.standings:
        facts.append(
            {
                "type": "standing",
                "league_code": bundle.meta.code,
                "team": row.team,
                "payload": {
                    "rank": row.rank,
                    "played": row.played,
                    "wins": row.wins,
                    "draws": row.draws,
                    "losses": row.losses,
                    "goals_for": row.goals_for,
                    "goals_against": row.goals_against,
                    "points": row.points,
                },
                "source_url": sources[0],
                "source_name": "BBC Sport",
                "credibility": 0.9,
                "observed_at": datetime.utcnow().isoformat(),
            }
        )

    for fixture in bundle.fixtures:
        facts.append(
            {
                "type": "fixture",
                "league_code": bundle.meta.code,
                "team": None,
                "payload": {
                    "home": fixture.home,
                    "away": fixture.away,
                    "kickoff_local": fixture.kickoff_local.isoformat() if fixture.kickoff_local else None,
                    "kickoff_utc": fixture.kickoff_utc.isoformat() if fixture.kickoff_utc else None,
                },
                "source_url": sources[1],
                "source_name": "BBC Sport",
                "credibility": 0.85,
                "observed_at": datetime.utcnow().isoformat(),
            }
        )

    for scorer in bundle.top_scorers:
        facts.append(
            {
                "type": "top_scorer",
                "league_code": bundle.meta.code,
                "team": scorer.team,
                "payload": {
                    "player": scorer.player,
                    "team": scorer.team,
                    "goals": scorer.goals,
                },
                "source_url": sources[2],
                "source_name": "BBC Sport",
                "credibility": 0.88,
                "observed_at": datetime.utcnow().isoformat(),
            }
        )

    payload = {
        "league_code": bundle.meta.code,
        "league_name": bundle.meta.name,
        "table": [row.__dict__ for row in bundle.standings],
        "fixtures_next": [_fixture_payload(f) for f in bundle.fixtures],
        "top_scorers": [
            {"player": scorer.player, "team": scorer.team, "goals": scorer.goals}
            for scorer in bundle.top_scorers
        ],
    }
    payload["sources_used"] = sources

    return NormalizedFacts(facts=facts, payload=payload, sources=sources)


def _fixture_payload(fixture: FixtureRow) -> Dict:
    return {
        "home": fixture.home,
        "away": fixture.away,
        "kickoff_local": fixture.kickoff_local.isoformat() if fixture.kickoff_local else None,
        "kickoff_utc": fixture.kickoff_utc.isoformat() if fixture.kickoff_utc else None,
    }
