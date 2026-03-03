import json
import os
from parser.clm_parser import parse_clm_export, CLMParseError


FIXTURE_PATH = os.path.join(os.path.dirname(__file__), "fixtures", "sample_clm_export.json")


def load_fixture():
    with open(FIXTURE_PATH) as f:
        return f.read()


def test_parse_returns_players_loot_history():
    players, loot, history = parse_clm_export(load_fixture())
    assert len(players) == 3
    assert len(loot) == 2
    assert len(history) == 3


def test_parse_player_fields():
    players, _, _ = parse_clm_export(load_fixture())
    legolas = next(p for p in players if p.name == "Legolas")
    assert legolas.wow_class == "Hunter"
    assert legolas.dkp == 150.0
    assert legolas.dkp_gained == 500.0
    assert legolas.dkp_spent == 350.0


def test_parse_loot_fields():
    _, loot, _ = parse_clm_export(load_fixture())
    entry = next(e for e in loot if e.item_name == "Warp Slicer")
    assert entry.player_name == "Legolas"
    assert entry.item_id == 30311
    assert entry.dkp_cost == 100.0


def test_parse_history_fields():
    _, _, history = parse_clm_export(load_fixture())
    entry = next(e for e in history if e.player_name == "Aragorn")
    assert entry.dkp_change == -50.0
    assert entry.reason == "Decay"


def test_parse_invalid_json():
    try:
        parse_clm_export("not json at all")
        assert False, "Should have raised CLMParseError"
    except CLMParseError:
        pass


def test_parse_missing_standings_key():
    data = json.dumps({"metadata": {}, "loot": [], "history": []})
    try:
        parse_clm_export(data)
        assert False, "Should have raised CLMParseError"
    except CLMParseError:
        pass
