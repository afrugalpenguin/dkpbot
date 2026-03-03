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
    if not players:
        embed.description = "No data available."
        return embed

    mid = (len(players) + 1) // 2
    left = players[:mid]
    right = players[mid:]

    left_lines = []
    for i, p in enumerate(left, 1):
        left_lines.append(f"**{i}.** {p.name} ({p.wow_class}) — **{p.dkp:.0f}**")

    right_lines = []
    for i, p in enumerate(right, mid + 1):
        right_lines.append(f"**{i}.** {p.name} ({p.wow_class}) — **{p.dkp:.0f}**")

    embed.add_field(name="Rank", value="\n".join(left_lines), inline=True)
    if right_lines:
        embed.add_field(name="\u200b", value="\n".join(right_lines), inline=True)

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
