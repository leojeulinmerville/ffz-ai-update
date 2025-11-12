import logging

from fastapi import APIRouter, HTTPException

from app.data.extractor.leagues import fetch_league_teams
from app.data.sources_catalog import get_league_meta, list_leagues

router = APIRouter(prefix="/meta", tags=["meta"])
logger = logging.getLogger(__name__)


@router.get("/leagues")
async def list_leagues_endpoint():
    return {"leagues": list_leagues()}


@router.get("/leagues/{league_code}/teams")
async def list_league_teams_endpoint(league_code: str):
    meta = get_league_meta(league_code)
    if not meta:
        raise HTTPException(status_code=404, detail="Unsupported league code")
    try:
        teams = await fetch_league_teams(league_code)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - network failure
        logger.exception("Failed to load teams for %s: %s", league_code, exc)
        raise HTTPException(status_code=502, detail="Unable to fetch league teams") from exc
    return {"league_code": meta.code, "teams": [{"name": name} for name in teams]}
