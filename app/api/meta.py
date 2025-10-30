from fastapi import APIRouter

from app.data.football_provider import get_league_context

router = APIRouter(tags=["meta"])

LEAGUE_CATALOG = [
    {"code": "PL", "name": "Premier League", "country": "England"},
    {"code": "FL1", "name": "Ligue 1", "country": "France"},
    {"code": "SA", "name": "Serie A", "country": "Italy"},
    {"code": "BL1", "name": "Bundesliga", "country": "Germany"},
    {"code": "PD", "name": "LaLiga", "country": "Spain"},
    {"code": "CL", "name": "UEFA Champions League", "country": "Europe"},
]


@router.get("/meta/leagues")
async def list_leagues():
    return {"leagues": LEAGUE_CATALOG}


@router.get("/meta/leagues/{league_code}/teams")
async def list_league_teams_endpoint(league_code: str):
    league = await get_league_context(league_code)
    teams = league.get("teams") or []
    return {"league_code": league_code.upper(), "teams": teams}
