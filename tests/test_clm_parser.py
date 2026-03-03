import json
import os
from parser.clm_parser import parse_clm_export, get_roster_names, CLMParseError


FIXTURE_PATH = os.path.join(os.path.dirname(__file__), "fixtures", "sample_clm_export.json")


def load_fixture():
    with open(FIXTURE_PATH, encoding="utf-8") as f:
        return f.read()


def test_get_roster_names():
    names = get_roster_names(load_fixture())
    assert "Inept" in names


def test_parse_returns_players_loot_history():
    players, loot, history = parse_clm_export(load_fixture(), roster_name="Inept")
    assert len(players) == 27
    assert len(loot) == 0  # no loot in real export yet
    assert len(history) == 82


def test_parse_player_fields():
    players, _, _ = parse_clm_export(load_fixture(), roster_name="Inept")
    castborn = next(p for p in players if p.name == "Castborn")
    assert castborn.wow_class == "Mage"
    assert castborn.dkp == 150.0


def test_parse_history_fields():
    _, _, history = parse_clm_export(load_fixture(), roster_name="Inept")
    entry = next(e for e in history if e.player_name == "Castborn")
    assert entry.dkp_change == 150.0
    assert entry.reason == "Manual adjustment"
    assert entry.awarded_by == "Medus\u00e1"


def test_parse_invalid_json():
    try:
        parse_clm_export("not json at all")
        assert False, "Should have raised CLMParseError"
    except CLMParseError:
        pass


def test_parse_missing_standings_key():
    data = json.dumps({"metadata": {}, "lootHistory": {}, "pointHistory": {}})
    try:
        parse_clm_export(data)
        assert False, "Should have raised CLMParseError"
    except CLMParseError:
        pass


def test_parse_multiple_rosters_no_name_raises():
    """When multiple rosters exist and no name is given, should error."""
    raw = load_fixture()
    data = json.loads(raw)
    # Real export has 2 rosters, so parsing without roster_name should fail
    if len(data["standings"]["roster"]) > 1:
        try:
            parse_clm_export(raw)
            assert False, "Should have raised CLMParseError"
        except CLMParseError as e:
            assert "Multiple rosters" in str(e)


def test_parse_wrong_roster_name_raises():
    try:
        parse_clm_export(load_fixture(), roster_name="NonExistent")
        assert False, "Should have raised CLMParseError"
    except CLMParseError as e:
        assert "not found" in str(e)
