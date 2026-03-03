from models import Player, LootEntry, HistoryEntry
from datetime import datetime


def test_player_creation():
    p = Player(name="Legolas", wow_class="Hunter", dkp=150.0, dkp_gained=500.0, dkp_spent=350.0)
    assert p.name == "Legolas"
    assert p.wow_class == "Hunter"
    assert p.dkp == 150.0
    assert p.dkp_gained == 500.0
    assert p.dkp_spent == 350.0


def test_player_sorting():
    p1 = Player(name="Legolas", wow_class="Hunter", dkp=150.0)
    p2 = Player(name="Gandalf", wow_class="Mage", dkp=200.0)
    ranked = sorted([p1, p2], key=lambda p: p.dkp, reverse=True)
    assert ranked[0].name == "Gandalf"


def test_loot_entry_creation():
    ts = datetime(2026, 3, 1, 20, 30, 0)
    entry = LootEntry(
        player_name="Legolas",
        player_class="Hunter",
        item_id=30311,
        item_name="Warp Slicer",
        dkp_cost=100.0,
        timestamp=ts,
    )
    assert entry.player_name == "Legolas"
    assert entry.item_id == 30311
    assert entry.dkp_cost == 100.0
    assert entry.timestamp == ts


def test_history_entry_creation():
    ts = datetime(2026, 3, 1, 21, 0, 0)
    entry = HistoryEntry(
        player_name="Legolas",
        player_class="Hunter",
        dkp_change=25.0,
        reason="Void Reaver Kill",
        awarded_by="Gandalf",
        timestamp=ts,
    )
    assert entry.dkp_change == 25.0
    assert entry.reason == "Void Reaver Kill"
    assert entry.awarded_by == "Gandalf"
