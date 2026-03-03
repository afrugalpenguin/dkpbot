# DKPBot Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a Discord bot that parses CLM JSON exports and lets guild members query DKP standings, loot history, and related data via slash commands.

**Architecture:** discord.py v2.x cog-based bot. Upload channel watches for JSON attachments, parses into dataclasses, stores in-memory with pickle persistence. Slash commands query the store and return paginated embeds.

**Tech Stack:** Python 3.11+, discord.py 2.x, pytest, Railway (Procfile)

---

### Task 1: Project Bootstrap

**Files:**
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `Procfile`

**Step 1: Create requirements.txt**

```
discord.py>=2.3,<3.0
python-dotenv>=1.0
```

**Step 2: Create .env.example**

```
DISCORD_TOKEN=your-bot-token-here
```

**Step 3: Create Procfile for Railway**

```
worker: python bot.py
```

**Step 4: Create virtual environment and install deps**

Run: `python -m venv venv && source venv/Scripts/activate && pip install -r requirements.txt`

**Step 5: Install test dependencies**

Run: `pip install pytest pytest-asyncio`

**Step 6: Commit**

```bash
git add requirements.txt .env.example Procfile
git commit -m "chore(init): add requirements, env template, and Procfile"
```

---

### Task 2: Data Models

**Files:**
- Create: `tests/test_models.py`
- Create: `models.py`

**Step 1: Write failing tests**

```python
# tests/test_models.py
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
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_models.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'models'`

**Step 3: Implement models**

```python
# models.py
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Player:
    name: str
    wow_class: str
    dkp: float = 0.0
    dkp_gained: float = 0.0
    dkp_spent: float = 0.0


@dataclass
class LootEntry:
    player_name: str
    player_class: str
    item_id: int
    item_name: str
    dkp_cost: float
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class HistoryEntry:
    player_name: str
    player_class: str
    dkp_change: float
    reason: str
    awarded_by: str
    timestamp: datetime = field(default_factory=datetime.now)
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_models.py -v`
Expected: 4 passed

**Step 5: Commit**

```bash
git add models.py tests/test_models.py
git commit -m "feat(models): add Player, LootEntry, HistoryEntry dataclasses"
```

---

### Task 3: Data Store

**Files:**
- Create: `tests/test_store.py`
- Create: `store.py`

**Step 1: Write failing tests**

```python
# tests/test_store.py
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
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_store.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'store'`

**Step 3: Implement store**

```python
# store.py
import pickle
from datetime import datetime
from typing import Optional
from models import Player, LootEntry, HistoryEntry


class GuildStore:
    def __init__(self):
        self.players: list[Player] = []
        self.loot: list[LootEntry] = []
        self.history: list[HistoryEntry] = []
        self.updated_at: Optional[datetime] = None
        self._player_lookup: dict[str, Player] = {}

    def load_data(self, players: list[Player], loot: list[LootEntry],
                  history: list[HistoryEntry]):
        self.players = players
        self.loot = sorted(loot, key=lambda e: e.timestamp, reverse=True)
        self.history = sorted(history, key=lambda e: e.timestamp, reverse=True)
        self.updated_at = datetime.now()
        self._player_lookup = {p.name.lower(): p for p in players}

    def get_player(self, name: str) -> Optional[Player]:
        return self._player_lookup.get(name.lower())

    def get_players_by_class(self, wow_class: str) -> list[Player]:
        wow_class_lower = wow_class.lower()
        return sorted(
            [p for p in self.players if p.wow_class.lower() == wow_class_lower],
            key=lambda p: p.dkp, reverse=True,
        )

    def get_standings(self) -> list[Player]:
        return sorted(self.players, key=lambda p: p.dkp, reverse=True)

    def get_loot(self, player_name: Optional[str] = None) -> list[LootEntry]:
        if player_name:
            name_lower = player_name.lower()
            return [e for e in self.loot if e.player_name.lower() == name_lower]
        return self.loot

    def get_history(self, player_name: Optional[str] = None) -> list[HistoryEntry]:
        if player_name:
            name_lower = player_name.lower()
            return [e for e in self.history if e.player_name.lower() == name_lower]
        return self.history

    def search_loot(self, item_query: str) -> list[LootEntry]:
        query_lower = item_query.lower()
        return [e for e in self.loot if query_lower in e.item_name.lower()]

    def get_raid_loot(self, date: Optional[datetime] = None) -> list[LootEntry]:
        if not self.loot:
            return []
        if date:
            return [e for e in self.loot if e.timestamp.date() == date.date()]
        latest_date = self.loot[0].timestamp.date()
        return [e for e in self.loot if e.timestamp.date() == latest_date]

    def save_to_disk(self, path: str):
        with open(path, "wb") as f:
            pickle.dump(self, f)

    @staticmethod
    def load_from_disk(path: str) -> "GuildStore":
        with open(path, "rb") as f:
            return pickle.load(f)
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_store.py -v`
Expected: 12 passed

**Step 5: Commit**

```bash
git add store.py tests/test_store.py
git commit -m "feat(store): add GuildStore with query methods and pickle persistence"
```

---

### Task 4: CLM JSON Parser (Mock Schema)

**Files:**
- Create: `tests/test_clm_parser.py`
- Create: `tests/fixtures/sample_clm_export.json`
- Create: `parser/__init__.py`
- Create: `parser/clm_parser.py`

**Step 1: Create sample fixture**

We don't have the real CLM export yet, so define a reasonable mock schema. This will be updated when we get a real export.

```json
{
    "metadata": {
        "addon": "ClassicLootManager",
        "export_date": "2026-03-01T21:00:00",
        "guild": "The Fellowship",
        "server": "Faerlina"
    },
    "standings": [
        {"name": "Legolas", "class": "Hunter", "dkp": 150.0, "gained": 500.0, "spent": 350.0},
        {"name": "Gandalf", "class": "Mage", "dkp": 200.0, "gained": 400.0, "spent": 200.0},
        {"name": "Aragorn", "class": "Warrior", "dkp": 175.0, "gained": 300.0, "spent": 125.0}
    ],
    "loot": [
        {"player": "Legolas", "class": "Hunter", "item_id": 30311, "item_name": "Warp Slicer", "cost": 100.0, "timestamp": "2026-03-01T20:30:00"},
        {"player": "Gandalf", "class": "Mage", "item_id": 30310, "item_name": "Staff of Disintegration", "cost": 150.0, "timestamp": "2026-03-01T20:45:00"}
    ],
    "history": [
        {"player": "Legolas", "class": "Hunter", "change": 25.0, "reason": "Void Reaver Kill", "awarded_by": "Gandalf", "timestamp": "2026-03-01T21:00:00"},
        {"player": "Gandalf", "class": "Mage", "change": 25.0, "reason": "Void Reaver Kill", "awarded_by": "Gandalf", "timestamp": "2026-03-01T21:00:00"},
        {"player": "Aragorn", "class": "Warrior", "change": -50.0, "reason": "Decay", "awarded_by": "System", "timestamp": "2026-03-01T22:00:00"}
    ]
}
```

**Step 2: Write failing tests**

```python
# tests/test_clm_parser.py
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
```

**Step 3: Run tests to verify they fail**

Run: `pytest tests/test_clm_parser.py -v`
Expected: FAIL — `ModuleNotFoundError`

**Step 4: Implement parser**

```python
# parser/__init__.py
```

```python
# parser/clm_parser.py
import json
from datetime import datetime
from models import Player, LootEntry, HistoryEntry


class CLMParseError(Exception):
    pass


def parse_clm_export(raw_json: str) -> tuple[list[Player], list[LootEntry], list[HistoryEntry]]:
    try:
        data = json.loads(raw_json)
    except json.JSONDecodeError as e:
        raise CLMParseError(f"Invalid JSON: {e}")

    if "standings" not in data:
        raise CLMParseError("Missing 'standings' key in export data")
    if "loot" not in data:
        raise CLMParseError("Missing 'loot' key in export data")
    if "history" not in data:
        raise CLMParseError("Missing 'history' key in export data")

    players = [
        Player(
            name=entry["name"],
            wow_class=entry["class"],
            dkp=float(entry.get("dkp", 0)),
            dkp_gained=float(entry.get("gained", 0)),
            dkp_spent=float(entry.get("spent", 0)),
        )
        for entry in data["standings"]
    ]

    loot = [
        LootEntry(
            player_name=entry["player"],
            player_class=entry["class"],
            item_id=int(entry["item_id"]),
            item_name=entry["item_name"],
            dkp_cost=float(entry["cost"]),
            timestamp=datetime.fromisoformat(entry["timestamp"]),
        )
        for entry in data["loot"]
    ]

    history = [
        HistoryEntry(
            player_name=entry["player"],
            player_class=entry["class"],
            dkp_change=float(entry["change"]),
            reason=entry["reason"],
            awarded_by=entry["awarded_by"],
            timestamp=datetime.fromisoformat(entry["timestamp"]),
        )
        for entry in data["history"]
    ]

    return players, loot, history
```

**Step 5: Run tests to verify they pass**

Run: `pytest tests/test_clm_parser.py -v`
Expected: 6 passed

**Step 6: Commit**

```bash
git add parser/ tests/test_clm_parser.py tests/fixtures/
git commit -m "feat(parser): add CLM JSON parser with mock schema"
```

---

### Task 5: Display Helpers

**Files:**
- Create: `tests/test_display.py`
- Create: `display.py`

**Step 1: Write failing tests**

```python
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
    assert len(embed.fields) > 0


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
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_display.py -v`
Expected: FAIL

**Step 3: Implement display helpers**

```python
# display.py
import discord
from datetime import datetime
from typing import Optional
from models import Player, LootEntry, HistoryEntry


CLASS_COLORS = {
    "Druid": 0xFF7D0A,
    "Hunter": 0xABD473,
    "Mage": 0x69CCF0,
    "Paladin": 0xF58CBA,
    "Priest": 0xFFFFFF,
    "Rogue": 0xFFF569,
    "Shaman": 0x0070DE,
    "Warlock": 0x9482C9,
    "Warrior": 0xC79C6E,
}

DEFAULT_COLOR = 0x808080


def class_color(wow_class: str) -> int:
    return CLASS_COLORS.get(wow_class, DEFAULT_COLOR)


def format_standings_embed(players: list[Player], title: str = "DKP Standings",
                           updated_at: Optional[datetime] = None) -> discord.Embed:
    embed = discord.Embed(title=title, color=0x5865F2)
    lines = []
    for i, p in enumerate(players, 1):
        lines.append(f"**{i}.** {p.name} ({p.wow_class}) — **{p.dkp:.0f}** DKP")
    embed.description = "\n".join(lines) if lines else "No data available."
    if updated_at:
        embed.set_footer(text=f"Last updated: {updated_at:%Y-%m-%d %H:%M}")
    return embed


def format_loot_embed(loot: list[LootEntry], title: str = "Loot History",
                      updated_at: Optional[datetime] = None) -> discord.Embed:
    embed = discord.Embed(title=title, color=0xE6CC80)
    lines = []
    for entry in loot:
        item_link = f"[{entry.item_name}](https://tbc.wowhead.com/item={entry.item_id})"
        lines.append(
            f"{item_link} — {entry.player_name} ({entry.player_class}) "
            f"for **{entry.dkp_cost:.0f}** DKP "
            f"<t:{int(entry.timestamp.timestamp())}:R>"
        )
    embed.description = "\n".join(lines) if lines else "No loot records."
    if updated_at:
        embed.set_footer(text=f"Last updated: {updated_at:%Y-%m-%d %H:%M}")
    return embed


def format_history_embed(history: list[HistoryEntry], title: str = "DKP History",
                         updated_at: Optional[datetime] = None) -> discord.Embed:
    embed = discord.Embed(title=title, color=0x57F287)
    lines = []
    for entry in history:
        sign = "+" if entry.dkp_change >= 0 else ""
        lines.append(
            f"{entry.player_name} ({entry.player_class}): "
            f"**{sign}{entry.dkp_change:.0f}** — {entry.reason} "
            f"(by {entry.awarded_by}) "
            f"<t:{int(entry.timestamp.timestamp())}:R>"
        )
    embed.description = "\n".join(lines) if lines else "No history records."
    if updated_at:
        embed.set_footer(text=f"Last updated: {updated_at:%Y-%m-%d %H:%M}")
    return embed
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_display.py -v`
Expected: 5 passed

**Step 5: Commit**

```bash
git add display.py tests/test_display.py
git commit -m "feat(display): add embed formatters with class colors and Wowhead links"
```

---

### Task 6: Pagination View

**Files:**
- Create: `tests/test_pagination.py`
- Create: `pagination.py`

**Step 1: Write failing tests**

```python
# tests/test_pagination.py
from pagination import paginate_list


def test_paginate_single_page():
    items = list(range(5))
    pages = paginate_list(items, per_page=10)
    assert len(pages) == 1
    assert pages[0] == [0, 1, 2, 3, 4]


def test_paginate_multiple_pages():
    items = list(range(25))
    pages = paginate_list(items, per_page=10)
    assert len(pages) == 3
    assert len(pages[0]) == 10
    assert len(pages[1]) == 10
    assert len(pages[2]) == 5


def test_paginate_empty():
    pages = paginate_list([], per_page=10)
    assert len(pages) == 1
    assert pages[0] == []


def test_paginate_exact_fit():
    items = list(range(10))
    pages = paginate_list(items, per_page=10)
    assert len(pages) == 1
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_pagination.py -v`
Expected: FAIL

**Step 3: Implement pagination**

```python
# pagination.py
import discord
from typing import Any


def paginate_list(items: list, per_page: int = 10) -> list[list]:
    if not items:
        return [[]]
    return [items[i:i + per_page] for i in range(0, len(items), per_page)]


class PaginationView(discord.ui.View):
    def __init__(self, pages: list[discord.Embed], timeout: float = 120.0):
        super().__init__(timeout=timeout)
        self.pages = pages
        self.current_page = 0
        self._update_buttons()

    def _update_buttons(self):
        self.prev_button.disabled = self.current_page == 0
        self.next_button.disabled = self.current_page >= len(self.pages) - 1

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.secondary)
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page -= 1
        self._update_buttons()
        await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.secondary)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page += 1
        self._update_buttons()
        await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_pagination.py -v`
Expected: 4 passed

**Step 5: Commit**

```bash
git add pagination.py tests/test_pagination.py
git commit -m "feat(pagination): add list paginator and PaginationView for embeds"
```

---

### Task 7: Admin Cog (Upload Handling + Config)

**Files:**
- Create: `cogs/__init__.py`
- Create: `cogs/admin.py`

No unit tests for cogs — they interact with Discord API directly. Will be tested manually.

**Step 1: Create cog**

```python
# cogs/__init__.py
```

```python
# cogs/admin.py
import discord
from discord import app_commands
from discord.ext import commands
from parser.clm_parser import parse_clm_export, CLMParseError


class AdminCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def is_admin(self, interaction: discord.Interaction) -> bool:
        admin_role_id = self.bot.guild_configs.get(interaction.guild_id, {}).get("admin_role_id")
        if admin_role_id:
            return any(r.id == admin_role_id for r in interaction.user.roles)
        return interaction.user.guild_permissions.administrator

    config_group = app_commands.Group(name="config", description="Bot configuration")

    @config_group.command(name="upload_channel", description="Set the channel for DKP data uploads")
    @app_commands.describe(channel="The channel to watch for CLM export uploads")
    async def set_upload_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        if not self.is_admin(interaction):
            await interaction.response.send_message("You don't have permission to do that.", ephemeral=True)
            return
        guild_id = interaction.guild_id
        if guild_id not in self.bot.guild_configs:
            self.bot.guild_configs[guild_id] = {}
        self.bot.guild_configs[guild_id]["upload_channel_id"] = channel.id
        self.bot.save_configs()
        await interaction.response.send_message(f"Upload channel set to {channel.mention}", ephemeral=True)

    @config_group.command(name="admin_role", description="Set the admin role for bot management")
    @app_commands.describe(role="The role that can manage the bot")
    async def set_admin_role(self, interaction: discord.Interaction, role: discord.Role):
        if not self.is_admin(interaction):
            await interaction.response.send_message("You don't have permission to do that.", ephemeral=True)
            return
        guild_id = interaction.guild_id
        if guild_id not in self.bot.guild_configs:
            self.bot.guild_configs[guild_id] = {}
        self.bot.guild_configs[guild_id]["admin_role_id"] = role.id
        self.bot.save_configs()
        await interaction.response.send_message(f"Admin role set to {role.mention}", ephemeral=True)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        if not message.attachments:
            return
        guild_id = message.guild.id if message.guild else None
        if not guild_id:
            return
        upload_channel_id = self.bot.guild_configs.get(guild_id, {}).get("upload_channel_id")
        if not upload_channel_id or message.channel.id != upload_channel_id:
            return

        for attachment in message.attachments:
            if not attachment.filename.endswith(".json"):
                continue
            try:
                raw = await attachment.read()
                raw_text = raw.decode("utf-8")
                players, loot, history = parse_clm_export(raw_text)
                self.bot.guild_stores[guild_id].load_data(players, loot, history)
                self.bot.save_store(guild_id)
                store = self.bot.guild_stores[guild_id]
                await message.reply(
                    f"DKP data updated — **{len(store.players)}** players, "
                    f"**{len(store.loot)}** loot entries, "
                    f"**{len(store.history)}** history records."
                )
            except CLMParseError as e:
                await message.reply(f"Failed to parse CLM export: {e}")
            except Exception as e:
                await message.reply(f"Error processing file: {e}")


async def setup(bot: commands.Bot):
    await bot.add_cog(AdminCog(bot))
```

**Step 2: Commit**

```bash
git add cogs/
git commit -m "feat(admin): add admin cog with upload handling and config commands"
```

---

### Task 8: Query Cog (Slash Commands)

**Files:**
- Create: `cogs/queries.py`

**Step 1: Create cog**

```python
# cogs/queries.py
import discord
from discord import app_commands
from discord.ext import commands
from display import format_standings_embed, format_loot_embed, format_history_embed
from pagination import paginate_list, PaginationView

ITEMS_PER_PAGE = 15


class QueryCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def get_store(self, guild_id: int):
        return self.bot.guild_stores.get(guild_id)

    @app_commands.command(name="dkp", description="Check DKP standings")
    @app_commands.describe(player="Player name", wow_class="WoW class to filter by")
    async def dkp(self, interaction: discord.Interaction, player: str = None,
                  wow_class: str = None):
        store = self.get_store(interaction.guild_id)
        if not store or not store.players:
            await interaction.response.send_message("No DKP data loaded yet.", ephemeral=True)
            return

        if player:
            p = store.get_player(player)
            if not p:
                await interaction.response.send_message(f"Player '{player}' not found.", ephemeral=True)
                return
            embed = format_standings_embed([p], title=f"DKP — {p.name}",
                                           updated_at=store.updated_at)
            await interaction.response.send_message(embed=embed)
        elif wow_class:
            players = store.get_players_by_class(wow_class)
            if not players:
                await interaction.response.send_message(f"No players found for class '{wow_class}'.", ephemeral=True)
                return
            pages_data = paginate_list(players, per_page=ITEMS_PER_PAGE)
            embeds = [format_standings_embed(page, title=f"DKP — {wow_class}",
                                             updated_at=store.updated_at) for page in pages_data]
            if len(embeds) == 1:
                await interaction.response.send_message(embed=embeds[0])
            else:
                view = PaginationView(embeds)
                await interaction.response.send_message(embed=embeds[0], view=view)
        else:
            standings = store.get_standings()
            pages_data = paginate_list(standings, per_page=ITEMS_PER_PAGE)
            embeds = [format_standings_embed(page, title="DKP Standings",
                                             updated_at=store.updated_at) for page in pages_data]
            if len(embeds) == 1:
                await interaction.response.send_message(embed=embeds[0])
            else:
                view = PaginationView(embeds)
                await interaction.response.send_message(embed=embeds[0], view=view)

    @app_commands.command(name="loot", description="View loot history")
    @app_commands.describe(player="Filter by player name")
    async def loot(self, interaction: discord.Interaction, player: str = None):
        store = self.get_store(interaction.guild_id)
        if not store or not store.loot:
            await interaction.response.send_message("No loot data loaded yet.", ephemeral=True)
            return

        loot = store.get_loot(player_name=player)
        if not loot:
            await interaction.response.send_message("No loot records found.", ephemeral=True)
            return

        title = f"Loot — {player}" if player else "Recent Loot"
        pages_data = paginate_list(loot, per_page=ITEMS_PER_PAGE)
        embeds = [format_loot_embed(page, title=title, updated_at=store.updated_at)
                  for page in pages_data]
        if len(embeds) == 1:
            await interaction.response.send_message(embed=embeds[0])
        else:
            view = PaginationView(embeds)
            await interaction.response.send_message(embed=embeds[0], view=view)

    @app_commands.command(name="history", description="View DKP transaction history")
    @app_commands.describe(player="Filter by player name")
    async def history(self, interaction: discord.Interaction, player: str = None):
        store = self.get_store(interaction.guild_id)
        if not store or not store.history:
            await interaction.response.send_message("No history data loaded yet.", ephemeral=True)
            return

        history = store.get_history(player_name=player)
        if not history:
            await interaction.response.send_message("No history records found.", ephemeral=True)
            return

        title = f"DKP History — {player}" if player else "DKP History"
        pages_data = paginate_list(history, per_page=ITEMS_PER_PAGE)
        embeds = [format_history_embed(page, title=title, updated_at=store.updated_at)
                  for page in pages_data]
        if len(embeds) == 1:
            await interaction.response.send_message(embed=embeds[0])
        else:
            view = PaginationView(embeds)
            await interaction.response.send_message(embed=embeds[0], view=view)

    @app_commands.command(name="item", description="Search loot records by item name")
    @app_commands.describe(name="Item name to search for")
    async def item(self, interaction: discord.Interaction, name: str):
        store = self.get_store(interaction.guild_id)
        if not store or not store.loot:
            await interaction.response.send_message("No loot data loaded yet.", ephemeral=True)
            return

        results = store.search_loot(name)
        if not results:
            await interaction.response.send_message(f"No loot records found matching '{name}'.", ephemeral=True)
            return

        pages_data = paginate_list(results, per_page=ITEMS_PER_PAGE)
        embeds = [format_loot_embed(page, title=f"Item Search — {name}",
                                     updated_at=store.updated_at) for page in pages_data]
        if len(embeds) == 1:
            await interaction.response.send_message(embed=embeds[0])
        else:
            view = PaginationView(embeds)
            await interaction.response.send_message(embed=embeds[0], view=view)

    @app_commands.command(name="raidloot", description="View loot from a specific raid")
    @app_commands.describe(date="Raid date (YYYY-MM-DD), defaults to most recent")
    async def raidloot(self, interaction: discord.Interaction, date: str = None):
        store = self.get_store(interaction.guild_id)
        if not store or not store.loot:
            await interaction.response.send_message("No loot data loaded yet.", ephemeral=True)
            return

        from datetime import datetime
        raid_date = None
        if date:
            try:
                raid_date = datetime.strptime(date, "%Y-%m-%d")
            except ValueError:
                await interaction.response.send_message(
                    "Invalid date format. Use YYYY-MM-DD.", ephemeral=True)
                return

        loot = store.get_raid_loot(date=raid_date)
        if not loot:
            await interaction.response.send_message("No loot found for that date.", ephemeral=True)
            return

        raid_date_str = loot[0].timestamp.strftime("%Y-%m-%d")
        title = f"Raid Loot — {raid_date_str}"
        pages_data = paginate_list(loot, per_page=ITEMS_PER_PAGE)
        embeds = [format_loot_embed(page, title=title, updated_at=store.updated_at)
                  for page in pages_data]
        if len(embeds) == 1:
            await interaction.response.send_message(embed=embeds[0])
        else:
            view = PaginationView(embeds)
            await interaction.response.send_message(embed=embeds[0], view=view)


async def setup(bot: commands.Bot):
    await bot.add_cog(QueryCog(bot))
```

**Step 2: Commit**

```bash
git add cogs/queries.py
git commit -m "feat(queries): add slash commands for dkp, loot, history, item, raidloot"
```

---

### Task 9: Bot Entry Point

**Files:**
- Create: `bot.py`
- Create: `tests/__init__.py`

**Step 1: Create bot.py**

```python
# bot.py
import json
import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from store import GuildStore

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
DATA_DIR = os.getenv("DATA_DIR", "data")


class DKPBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)
        self.guild_stores: dict[int, GuildStore] = {}
        self.guild_configs: dict[int, dict] = {}

    async def setup_hook(self):
        self.load_configs()
        self.load_all_stores()
        await self.load_extension("cogs.admin")
        await self.load_extension("cogs.queries")
        await self.tree.sync()

    async def on_ready(self):
        print(f"DKPBot online as {self.user} (ID: {self.user.id})")
        print(f"Serving {len(self.guilds)} guild(s)")

    def load_configs(self):
        path = os.path.join(DATA_DIR, "configs.json")
        if os.path.exists(path):
            with open(path) as f:
                raw = json.load(f)
                self.guild_configs = {int(k): v for k, v in raw.items()}

    def save_configs(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        path = os.path.join(DATA_DIR, "configs.json")
        with open(path, "w") as f:
            json.dump({str(k): v for k, v in self.guild_configs.items()}, f, indent=2)

    def load_all_stores(self):
        if not os.path.exists(DATA_DIR):
            return
        for filename in os.listdir(DATA_DIR):
            if filename.startswith("store_") and filename.endswith(".pkl"):
                guild_id = int(filename.replace("store_", "").replace(".pkl", ""))
                path = os.path.join(DATA_DIR, filename)
                try:
                    self.guild_stores[guild_id] = GuildStore.load_from_disk(path)
                except Exception as e:
                    print(f"Failed to load store for guild {guild_id}: {e}")

    def save_store(self, guild_id: int):
        os.makedirs(DATA_DIR, exist_ok=True)
        store = self.guild_stores.get(guild_id)
        if store:
            path = os.path.join(DATA_DIR, f"store_{guild_id}.pkl")
            store.save_to_disk(path)

    def ensure_store(self, guild_id: int) -> GuildStore:
        if guild_id not in self.guild_stores:
            self.guild_stores[guild_id] = GuildStore()
        return self.guild_stores[guild_id]


bot = DKPBot()

# Patch ensure_store into on_message flow
_original_on_message = None

@bot.listen("on_guild_join")
async def on_guild_join(guild: discord.Guild):
    bot.ensure_store(guild.id)


if __name__ == "__main__":
    if not TOKEN:
        print("Error: DISCORD_TOKEN environment variable not set.")
        print("Copy .env.example to .env and add your bot token.")
        exit(1)
    bot.run(TOKEN)
```

```python
# tests/__init__.py
```

**Step 2: Ensure the admin cog uses ensure_store**

Update `cogs/admin.py` on_message handler to use `self.bot.ensure_store(guild_id)` instead of directly accessing `self.bot.guild_stores[guild_id]`. Replace this line in the on_message listener:

```python
# Change:
self.bot.guild_stores[guild_id].load_data(players, loot, history)
# To:
self.bot.ensure_store(guild_id).load_data(players, loot, history)
```

**Step 3: Run all tests**

Run: `pytest -v`
Expected: All 27 tests pass

**Step 4: Commit**

```bash
git add bot.py tests/__init__.py
git commit -m "feat(bot): add bot entry point with config and store management"
```

---

### Task 10: Railway Deployment Files

**Files:**
- Verify: `Procfile`
- Verify: `requirements.txt`
- Verify: `.env.example`
- Create: `runtime.txt`

**Step 1: Create runtime.txt**

```
python-3.11
```

**Step 2: Verify Procfile content**

```
worker: python bot.py
```

The `worker` process type is important — Railway needs to know this is a long-running worker, not a web server.

**Step 3: Verify requirements.txt includes all deps**

```
discord.py>=2.3,<3.0
python-dotenv>=1.0
```

**Step 4: Run full test suite one final time**

Run: `pytest -v`
Expected: All tests pass

**Step 5: Commit**

```bash
git add runtime.txt
git commit -m "chore(deploy): add runtime.txt for Railway Python version"
```

---

### Summary

| Task | Component | Tests |
|------|-----------|-------|
| 1 | Project bootstrap | — |
| 2 | Data models | 4 |
| 3 | Data store | 12 |
| 4 | CLM JSON parser | 6 |
| 5 | Display helpers | 5 |
| 6 | Pagination | 4 |
| 7 | Admin cog | manual |
| 8 | Query cog | manual |
| 9 | Bot entry point | — |
| 10 | Railway deployment | — |

**Total: 10 tasks, ~27 automated tests**
