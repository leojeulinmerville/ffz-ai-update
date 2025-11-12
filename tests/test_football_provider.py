import asyncio

import asyncio

import pytest

from app.data import football_provider


def test_list_supported_leagues_non_empty():
    leagues = football_provider.list_supported_leagues()
    assert len(leagues) >= 1


def test_get_league_context_fallback(monkeypatch):
    monkeypatch.setattr(football_provider, "API_KEY", None)
    football_provider._league_cache.clear()
    league = asyncio.run(football_provider.get_league_context("FL1"))
    assert league["table"]
    assert league.get("teams")
