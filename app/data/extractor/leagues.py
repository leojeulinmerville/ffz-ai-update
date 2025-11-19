from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from zoneinfo import ZoneInfo

from selectolax.parser import HTMLParser

from app.config import TZ
from app.data.sources_catalog import LeagueMeta, get_league_meta
from app.services.http import fetch_text

EUROPE_TZ = ZoneInfo(TZ)


@dataclass
class StandingRow:
    rank: int
    team: str
    played: int
    wins: int
    draws: int
    losses: int
    goals_for: int
    goals_against: int
    points: int


@dataclass
class FixtureRow:
    home: str
    away: str
    kickoff_local: Optional[datetime]
    kickoff_utc: Optional[datetime]


@dataclass
class ScorerRow:
    player: str
    team: str
    goals: int


@dataclass
class LeagueBundle:
    meta: LeagueMeta
    standings: List[StandingRow]
    fixtures: List[FixtureRow]
    top_scorers: List[ScorerRow]


async def fetch_league_bundle(league_code: str) -> LeagueBundle:
    meta = get_league_meta(league_code)
    if not meta:
        raise ValueError(f"Unsupported league {league_code}")

    table_url = f"https://www.bbc.com/sport/football/{meta.bbc_slug}/table"
    scorers_url = f"https://www.bbc.com/sport/football/{meta.bbc_slug}/top-scorers"
    fixtures_url = f"https://www.bbc.com/sport/football/{meta.bbc_slug}/scores-fixtures"

    table_html, scorers_html, fixtures_html = await asyncio.gather(
        fetch_text(table_url),
        fetch_text(scorers_url),
        fetch_text(fixtures_url),
    )

    standings = parse_standings(table_html)
    fixtures = parse_fixtures(fixtures_html)
    scorers = parse_scorers(scorers_html)

    return LeagueBundle(
        meta=meta,
        standings=standings,
        fixtures=fixtures,
        top_scorers=scorers,
    )


async def fetch_league_teams(league_code: str) -> List[str]:
    meta = get_league_meta(league_code)
    if not meta:
        raise ValueError(f"Unsupported league {league_code}")
    table_url = f"https://www.bbc.com/sport/football/{meta.bbc_slug}/table"
    table_html = await fetch_text(table_url)
    standings = parse_standings(table_html)
    seen = []
    for row in standings:
        if row.team not in seen:
            seen.append(row.team)
    return seen


def parse_standings(html: str) -> List[StandingRow]:
    parser = HTMLParser(html)
    rows = parser.css("table tbody tr")
    standings: List[StandingRow] = []
    for row in rows:
        cells = row.css("td")
        if len(cells) < 9:
            continue
        team_link = cells[0].css_first("a")
        team_name = ""
        if team_link:
            team_name = team_link.text(strip=True)
        if not team_name:
            hidden = cells[0].css("span.visually-hidden")
            if hidden:
                team_name = hidden[-1].text(strip=True)
        if not team_name:
            continue

        rank_node = _find_span_with_class_fragment(row, "Rank")
        if rank_node:
            rank = _safe_int(rank_node.text(strip=True))
        else:
            rank = _extract_leading_int(cells[0].text(separator=" ", strip=True))
        played = _safe_int(cells[1].text(strip=True))
        wins = _safe_int(cells[2].text(strip=True))
        draws = _safe_int(cells[3].text(strip=True))
        losses = _safe_int(cells[4].text(strip=True))
        goals_for = _safe_int(cells[5].text(strip=True))
        goals_against = _safe_int(cells[6].text(strip=True))
        points_cell = cells[8].css_first("span") or cells[8]
        points = _safe_int(points_cell.text(strip=True))

        standings.append(
            StandingRow(
                rank=rank,
                team=team_name,
                played=played,
                wins=wins,
                draws=draws,
                losses=losses,
                goals_for=goals_for,
                goals_against=goals_against,
                points=points,
            )
        )
    return standings


def parse_scorers(html: str) -> List[ScorerRow]:
    parser = HTMLParser(html)
    rows = parser.css("table tbody tr")
    scorers: List[ScorerRow] = []
    for row in rows:
        cells = row.css("td")
        if len(cells) < 3:
            continue
        player_node = row.css_first(".ssrcss-m6ah29-PlayerName")
        team_node = row.css_first(".ssrcss-qvpga1-TeamsSummary")
        goals_node = cells[2]
        if not (player_node and team_node):
            continue
        player = player_node.text(strip=True)
        team = team_node.text(strip=True)
        goals = _safe_int(goals_node.text(strip=True))
        scorers.append(ScorerRow(player=player, team=team, goals=goals))
        if len(scorers) >= 20:
            break
    return scorers


def parse_fixtures(html: str) -> List[FixtureRow]:
    parser = HTMLParser(html)
    fixtures: List[FixtureRow] = []

    for heading in parser.css("h2"):
        date_value = _parse_heading_date(heading.text(strip=True))
        if not date_value:
            continue
        ul = _find_next_tag(heading, "ul")
        if not ul:
            continue
        containers = ul.css("[data-event-id]")
        for node in containers:
            team_blocks = node.css("[data-participant-id]")
            teams: List[str] = []
            for block in team_blocks[:2]:
                hidden = block.css_first("span.visually-hidden")
                if hidden:
                    name = hidden.text(strip=True)
                else:
                    name_parts = [el.text(strip=True) for el in block.css("span") if el.text(strip=True)]
                    name = name_parts[-1] if name_parts else ""
                if name:
                    teams.append(name)
            if len(teams) < 2:
                continue
            home, away = teams[0], teams[1]
            time_node = node.css_first("time")
            kickoff_local = None
            kickoff_utc = None
            if time_node:
                kickoff_local = _combine_date_time(date_value, time_node.text(strip=True))
                if kickoff_local:
                    kickoff_utc = kickoff_local.astimezone(timezone.utc)
            fixtures.append(
                FixtureRow(
                    home=home,
                    away=away,
                    kickoff_local=kickoff_local,
                    kickoff_utc=kickoff_utc,
                )
            )
            if len(fixtures) >= 20:
                break
    return fixtures


def _find_span_with_class_fragment(node, fragment: str):
    for span in node.css("span"):
        class_value = span.attributes.get("class", "")
        if fragment in class_value:
            return span
    return None


def _extract_leading_int(value: Optional[str]) -> int:
    if not value:
        return 0
    match = re.search(r"\d+", value)
    if not match:
        return 0
    return _safe_int(match.group(0))


def _parse_heading_date(text: str) -> Optional[datetime]:
    parts = text.split()
    if len(parts) < 3:
        return None
    weekday = parts[0]
    day = _strip_ordinal(parts[1])
    month = parts[2]
    year = datetime.now(EUROPE_TZ).year
    try:
        dt = datetime.strptime(f"{weekday} {day} {month} {year}", "%A %d %B %Y")
    except ValueError:
        return None
    dt = dt.replace(tzinfo=EUROPE_TZ)
    if dt < datetime.now(EUROPE_TZ) - timedelta(days=7):
        dt = dt.replace(year=year + 1)
    return dt


def _combine_date_time(date_value: datetime, time_text: str) -> Optional[datetime]:
    try:
        hours, minutes = time_text.strip().split(":")
        local_dt = date_value.replace(hour=int(hours), minute=int(minutes), second=0, microsecond=0)
        return local_dt
    except ValueError:
        return None


def _strip_ordinal(token: str) -> str:
    return re.sub(r"(st|nd|rd|th)$", "", token)


def _safe_int(value: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _find_next_tag(node, tag: str):
    cursor = node
    depth = 0
    while cursor and depth < 2000:
        cursor = cursor.next
        depth += 1
        if cursor is None:
            break
        if cursor.tag == tag:
            return cursor
    return None
