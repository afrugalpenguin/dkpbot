# tests/test_display.py
from display import class_color, format_standings_embed, format_loot_embed, format_history_embed
from models import Player, LootEntry, HistoryEntry
from datetime import datetime


def test_class_color_known():
    assert class_color("Hunter") == 0xABD473
    assert class_color("Mage") == 0x69CCF0
    assert class_color("Warrior") == 0xC79C6E


def test_class_color_unknown():
    assert class_color("Unknown") == 0x808080


def test_format_standings_embed():
    players = [
        Player(name="Gandalf", wow_class="Mage", dkp=200.0),
        Player(name="Legolas", wow_class="Hunter", dkp=150.0),
    ]
    embed = format_standings_embed(players, title="DKP Standings")
    assert embed.title == "DKP Standings"
    assert len(embed.fields) > 0 or embed.description


def test_format_loot_embed():
    loot = [
        LootEntry(player_name="Legolas", player_class="Hunter", item_id=30311,
                  item_name="Warp Slicer", dkp_cost=100.0,
                  timestamp=datetime(2026, 3, 1, 20, 30)),
    ]
    embed = format_loot_embed(loot, title="Recent Loot")
    assert embed.title == "Recent Loot"


def test_format_history_embed():
    history = [
        HistoryEntry(player_name="Legolas", player_class="Hunter",
                     dkp_change=25.0, reason="Boss Kill",
                     awarded_by="Gandalf", timestamp=datetime(2026, 3, 1, 21, 0)),
    ]
    embed = format_history_embed(history, title="DKP History")
    assert embed.title == "DKP History"
