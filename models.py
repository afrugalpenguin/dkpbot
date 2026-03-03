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
