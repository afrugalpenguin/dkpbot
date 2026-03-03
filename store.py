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

    TOKEN_GROUPS = {
        "Fallen Hero": ["Hunter", "Mage", "Warlock"],
        "Fallen Champion": ["Paladin", "Rogue", "Shaman"],
        "Fallen Defender": ["Druid", "Priest", "Warrior"],
    }

    def get_token_rivals(self, wow_class: str) -> tuple[Optional[str], list[Player]]:
        """Return (token_group_name, rivals) for the given class."""
        wow_class_title = wow_class.strip().title()
        for group_name, classes in self.TOKEN_GROUPS.items():
            if wow_class_title in classes:
                rivals = sorted(
                    [p for p in self.players if p.wow_class in classes],
                    key=lambda p: p.dkp, reverse=True,
                )
                return group_name, rivals
        return None, []

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
