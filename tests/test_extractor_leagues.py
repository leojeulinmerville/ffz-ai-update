from pathlib import Path

from app.data.extractor.leagues import parse_fixtures, parse_scorers, parse_standings


FIXTURE_DIR = Path(__file__).parent / "fixtures"


def test_parse_standings_from_fixture():
    fixture_path = FIXTURE_DIR / "bbc_table_sample.html"
    html = fixture_path.read_text(encoding="utf-8")
    standings = parse_standings(html)
    assert len(standings) == 2
    assert standings[0].team == "OGC Nice"
    assert standings[0].points == 20
    assert standings[1].team == "Paris SG"


def test_parse_fixtures_from_fixture():
    fixture_path = FIXTURE_DIR / "bbc_fixtures_sample.html"
    html = fixture_path.read_text(encoding="utf-8")
    fixtures = parse_fixtures(html)
    assert len(fixtures) == 2
    assert fixtures[0].home == "Arsenal"
    assert fixtures[0].away == "Chelsea"
    assert fixtures[0].kickoff_local is not None
    assert fixtures[0].kickoff_utc is not None


def test_parse_scorers_from_fixture():
    fixture_path = FIXTURE_DIR / "bbc_scorers_sample.html"
    html = fixture_path.read_text(encoding="utf-8")
    scorers = parse_scorers(html)
    assert len(scorers) == 2
    assert scorers[0].player == "E. Haaland"
    assert scorers[1].goals == 8
