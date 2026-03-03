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
