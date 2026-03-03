import json
from datetime import datetime
from models import Player, LootEntry, HistoryEntry


class CLMParseError(Exception):
    pass


def _find_roster(rosters: list[dict], roster_name: str) -> dict:
    """Find a roster by name."""
    for roster in rosters:
        if roster.get("name", "").lower() == roster_name.lower():
            return roster
    available = [r.get("name", "?") for r in rosters]
    raise CLMParseError(
        f"Roster '{roster_name}' not found. Available rosters: {', '.join(available)}"
    )


def get_roster_names(raw_json: str) -> list[str]:
    """Return available roster names from a CLM export."""
    try:
        data = json.loads(raw_json)
    except json.JSONDecodeError as e:
        raise CLMParseError(f"Invalid JSON: {e}")
    rosters = data.get("standings", {}).get("roster", [])
    return [r.get("name", "?") for r in rosters]


def parse_clm_export(raw_json: str, roster_name: str = None) -> tuple[list[Player], list[LootEntry], list[HistoryEntry]]:
    try:
        data = json.loads(raw_json)
    except json.JSONDecodeError as e:
        raise CLMParseError(f"Invalid JSON: {e}")

    if "standings" not in data:
        raise CLMParseError("Missing 'standings' key in export data")

    # Parse standings
    standings_rosters = data["standings"].get("roster", [])
    if not standings_rosters:
        raise CLMParseError("No roster found in standings data")

    if not roster_name:
        if len(standings_rosters) == 1:
            standings_roster = standings_rosters[0]
        else:
            available = [r.get("name", "?") for r in standings_rosters]
            raise CLMParseError(
                f"Multiple rosters found. Please configure one with "
                f"/dkp config roster. Available: {', '.join(available)}"
            )
    else:
        standings_roster = _find_roster(standings_rosters, roster_name)
    raw_players = standings_roster.get("standings", {}).get("player", [])

    # Build class lookup from standings for use in history
    class_lookup = {}
    players = []
    for entry in raw_players:
        name = entry["name"]
        wow_class = entry.get("class", "Unknown")
        class_lookup[name.lower()] = wow_class
        players.append(Player(
            name=name,
            wow_class=wow_class,
            dkp=float(entry.get("dkp", 0)),
        ))

    # Parse loot history
    loot = []
    loot_rosters = data.get("lootHistory", {}).get("roster", [])
    if loot_rosters and roster_name:
        loot_roster = _find_roster(loot_rosters, roster_name)
    elif loot_rosters:
        loot_roster = loot_rosters[0]
    else:
        loot_roster = None
    if loot_roster:
        raw_loot = loot_roster.get("lootHistory", {}).get("item", [])
        for entry in raw_loot:
            loot.append(LootEntry(
                player_name=entry.get("player", "Unknown"),
                player_class=class_lookup.get(entry.get("player", "").lower(), "Unknown"),
                item_id=int(entry.get("id", 0)),
                item_name=entry.get("name", "Unknown Item"),
                dkp_cost=float(entry.get("dkp", 0)),
                timestamp=datetime.fromtimestamp(entry.get("timestamp", 0)),
            ))

    # Parse point history
    history = []
    history_rosters = data.get("pointHistory", {}).get("roster", [])
    if history_rosters and roster_name:
        history_roster = _find_roster(history_rosters, roster_name)
    elif history_rosters:
        history_roster = history_rosters[0]
    else:
        history_roster = None
    if history_roster:
        raw_history = history_roster.get("pointHistory", {}).get("point", [])
        for entry in raw_history:
            player_name = entry.get("player", "Unknown")
            history.append(HistoryEntry(
                player_name=player_name,
                player_class=class_lookup.get(player_name.lower(), "Unknown"),
                dkp_change=float(entry.get("dkp", 0)),
                reason=entry.get("reason", ""),
                awarded_by=entry.get("awardedBy", "Unknown"),
                timestamp=datetime.fromtimestamp(entry.get("timestamp", 0)),
            ))

    return players, loot, history
