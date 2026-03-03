import os
import tempfile
from datetime import datetime
from store import GuildStore
from models import Player, LootEntry, HistoryEntry


def make_players():
    return [
        Player(name="Legolas", wow_class="Hunter", dkp=150.0, dkp_gained=500.0, dkp_spent=350.0),
        Player(name="Gandalf", wow_class="Mage", dkp=200.0, dkp_gained=400.0, dkp_spent=200.0),
        Player(name="Aragorn", wow_class="Warrior", dkp=175.0, dkp_gained=300.0, dkp_spent=125.0),
    ]


def make_loot():
    return [
        LootEntry(player_name="Legolas", player_class="Hunter", item_id=30311,
                  item_name="Warp Slicer", dkp_cost=100.0,
                  timestamp=datetime(2026, 3, 1, 20, 30)),
        LootEntry(player_name="Gandalf", player_class="Mage", item_id=30310,
                  item_name="Staff of Disintegration", dkp_cost=150.0,
                  timestamp=datetime(2026, 3, 1, 20, 45)),
    ]


def make_history():
    return [
        HistoryEntry(player_name="Legolas", player_class="Hunter", dkp_change=25.0,
                     reason="Void Reaver Kill", awarded_by="Gandalf",
                     timestamp=datetime(2026, 3, 1, 21, 0)),
    ]


def test_load_data():
    store = GuildStore()
    store.load_data(make_players(), make_loot(), make_history())
    assert len(store.players) == 3
    assert len(store.loot) == 2
    assert len(store.history) == 1
    assert store.updated_at is not None


def test_get_player():
    store = GuildStore()
    store.load_data(make_players(), make_loot(), make_history())
    p = store.get_player("Legolas")
    assert p is not None
    assert p.dkp == 150.0


def test_get_player_case_insensitive():
    store = GuildStore()
    store.load_data(make_players(), make_loot(), make_history())
    p = store.get_player("legolas")
    assert p is not None
    assert p.name == "Legolas"


def test_get_player_not_found():
    store = GuildStore()
    store.load_data(make_players(), make_loot(), make_history())
    assert store.get_player("Sauron") is None


def test_get_players_by_class():
    store = GuildStore()
    store.load_data(make_players(), make_loot(), make_history())
    hunters = store.get_players_by_class("Hunter")
    assert len(hunters) == 1
    assert hunters[0].name == "Legolas"


def test_get_standings_sorted_by_dkp():
    store = GuildStore()
    store.load_data(make_players(), make_loot(), make_history())
    standings = store.get_standings()
    assert standings[0].name == "Gandalf"
    assert standings[1].name == "Aragorn"
    assert standings[2].name == "Legolas"


def test_get_loot_for_player():
    store = GuildStore()
    store.load_data(make_players(), make_loot(), make_history())
    loot = store.get_loot(player_name="Legolas")
    assert len(loot) == 1
    assert loot[0].item_name == "Warp Slicer"


def test_get_loot_all():
    store = GuildStore()
    store.load_data(make_players(), make_loot(), make_history())
    loot = store.get_loot()
    assert len(loot) == 2


def test_get_history_for_player():
    store = GuildStore()
    store.load_data(make_players(), make_loot(), make_history())
    hist = store.get_history(player_name="Legolas")
    assert len(hist) == 1


def test_search_loot_by_item_name():
    store = GuildStore()
    store.load_data(make_players(), make_loot(), make_history())
    results = store.search_loot("Warp")
    assert len(results) == 1
    assert results[0].item_name == "Warp Slicer"


def test_search_loot_case_insensitive():
    store = GuildStore()
    store.load_data(make_players(), make_loot(), make_history())
    results = store.search_loot("warp")
    assert len(results) == 1


def test_pickle_persistence():
    store = GuildStore()
    store.load_data(make_players(), make_loot(), make_history())
    with tempfile.NamedTemporaryFile(suffix=".pkl", delete=False) as f:
        path = f.name
    try:
        store.save_to_disk(path)
        store2 = GuildStore.load_from_disk(path)
        assert len(store2.players) == 3
        assert len(store2.loot) == 2
        assert store2.updated_at == store.updated_at
    finally:
        os.unlink(path)
