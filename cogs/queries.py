# cogs/queries.py
import discord
from discord import app_commands
from discord.ext import commands
from display import format_standings_embed, format_loot_embed, format_history_embed
from pagination import paginate_list, PaginationView

ITEMS_PER_PAGE = 15

dkp_group = app_commands.Group(name="dkp", description="DKPBot commands")


def get_store(interaction: discord.Interaction):
    return interaction.client.guild_stores.get(interaction.guild_id)


@dkp_group.command(name="standings", description="Check DKP standings")
@app_commands.describe(player="Player name", wow_class="WoW class to filter by")
async def standings(interaction: discord.Interaction, player: str = None,
                    wow_class: str = None):
    store = get_store(interaction)
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
        await interaction.response.send_message(embed=embed, ephemeral=True)
    elif wow_class:
        players = store.get_players_by_class(wow_class)
        if not players:
            await interaction.response.send_message(f"No players found for class '{wow_class}'.", ephemeral=True)
            return
        embed = format_standings_embed(players, title=f"DKP — {wow_class}",
                                       updated_at=store.updated_at)
        await interaction.response.send_message(embed=embed, ephemeral=True)
    else:
        all_standings = store.get_standings()
        embed = format_standings_embed(all_standings, title="DKP Standings",
                                       updated_at=store.updated_at)
        await interaction.response.send_message(embed=embed, ephemeral=True)


@dkp_group.command(name="loot", description="View loot history")
@app_commands.describe(player="Filter by player name")
async def loot(interaction: discord.Interaction, player: str = None):
    store = get_store(interaction)
    if not store or not store.loot:
        await interaction.response.send_message("No loot data loaded yet.", ephemeral=True)
        return

    loot_entries = store.get_loot(player_name=player)
    if not loot_entries:
        await interaction.response.send_message("No loot records found.", ephemeral=True)
        return

    title = f"Loot — {player}" if player else "Recent Loot"
    pages_data = paginate_list(loot_entries, per_page=ITEMS_PER_PAGE)
    embeds = [format_loot_embed(page, title=title, updated_at=store.updated_at)
              for page in pages_data]
    if len(embeds) == 1:
        await interaction.response.send_message(embed=embeds[0], ephemeral=True)
    else:
        view = PaginationView(embeds)
        await interaction.response.send_message(embed=embeds[0], view=view, ephemeral=True)


@dkp_group.command(name="history", description="View DKP transaction history")
@app_commands.describe(player="Filter by player name")
async def history(interaction: discord.Interaction, player: str = None):
    store = get_store(interaction)
    if not store or not store.history:
        await interaction.response.send_message("No history data loaded yet.", ephemeral=True)
        return

    history_entries = store.get_history(player_name=player)
    if not history_entries:
        await interaction.response.send_message("No history records found.", ephemeral=True)
        return

    title = f"DKP History — {player}" if player else "DKP History"
    pages_data = paginate_list(history_entries, per_page=ITEMS_PER_PAGE)
    embeds = [format_history_embed(page, title=title, updated_at=store.updated_at)
              for page in pages_data]
    if len(embeds) == 1:
        await interaction.response.send_message(embed=embeds[0], ephemeral=True)
    else:
        view = PaginationView(embeds)
        await interaction.response.send_message(embed=embeds[0], view=view, ephemeral=True)


@dkp_group.command(name="item", description="Search loot records by item name")
@app_commands.describe(name="Item name to search for")
async def item(interaction: discord.Interaction, name: str):
    store = get_store(interaction)
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
        await interaction.response.send_message(embed=embeds[0], ephemeral=True)
    else:
        view = PaginationView(embeds)
        await interaction.response.send_message(embed=embeds[0], view=view, ephemeral=True)


@dkp_group.command(name="raidloot", description="View loot from a specific raid")
@app_commands.describe(date="Raid date (YYYY-MM-DD), defaults to most recent")
async def raidloot(interaction: discord.Interaction, date: str = None):
    store = get_store(interaction)
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

    loot_entries = store.get_raid_loot(date=raid_date)
    if not loot_entries:
        await interaction.response.send_message("No loot found for that date.", ephemeral=True)
        return

    raid_date_str = loot_entries[0].timestamp.strftime("%Y-%m-%d")
    title = f"Raid Loot — {raid_date_str}"
    pages_data = paginate_list(loot_entries, per_page=ITEMS_PER_PAGE)
    embeds = [format_loot_embed(page, title=title, updated_at=store.updated_at)
              for page in pages_data]
    if len(embeds) == 1:
        await interaction.response.send_message(embed=embeds[0], ephemeral=True)
    else:
        view = PaginationView(embeds)
        await interaction.response.send_message(embed=embeds[0], view=view, ephemeral=True)


@dkp_group.command(name="tokens", description="Show DKP standings for your token group")
@app_commands.describe(wow_class="Your WoW class")
async def tokens(interaction: discord.Interaction, wow_class: str):
    store = get_store(interaction)
    if not store or not store.players:
        await interaction.response.send_message("No DKP data loaded yet.", ephemeral=True)
        return

    group_name, rival_players = store.get_token_rivals(wow_class)
    if group_name is None:
        await interaction.response.send_message(
            f"Unknown class '{wow_class}'. Valid classes: Druid, Hunter, Mage, "
            "Paladin, Priest, Rogue, Shaman, Warlock, Warrior.", ephemeral=True)
        return
    if not rival_players:
        await interaction.response.send_message("No players found for that token group.", ephemeral=True)
        return

    embed = format_standings_embed(
        rival_players,
        title=f"{group_name} — Token Rivals",
        updated_at=store.updated_at,
    )
    await interaction.response.send_message(embed=embed)


@dkp_group.command(name="help", description="Show DKPBot commands and usage")
async def dkpbot_help(interaction: discord.Interaction):
    embed = discord.Embed(
        title="DKPBot",
        description="Discord bot for Classic Loot Manager DKP tracking.",
        color=0x5865F2,
    )
    embed.add_field(
        name="/dkp standings",
        value=(
            "`/dkp standings` — Full standings\n"
            "`/dkp standings player:Name` — Single player\n"
            "`/dkp standings wow_class:Hunter` — Filter by class"
        ),
        inline=False,
    )
    embed.add_field(
        name="/dkp loot",
        value=(
            "`/dkp loot` — Recent loot\n"
            "`/dkp loot player:Name` — Player's loot"
        ),
        inline=False,
    )
    embed.add_field(
        name="/dkp history",
        value=(
            "`/dkp history` — Recent history\n"
            "`/dkp history player:Name` — Player's history"
        ),
        inline=False,
    )
    embed.add_field(
        name="/dkp item",
        value="`/dkp item name:Netherblade` — Search loot by item name",
        inline=False,
    )
    embed.add_field(
        name="/dkp raidloot",
        value=(
            "`/dkp raidloot` — Most recent raid\n"
            "`/dkp raidloot date:2026-03-01` — Specific date"
        ),
        inline=False,
    )
    embed.add_field(
        name="/dkp tokens",
        value="`/dkp tokens wow_class:Hunter` — DKP standings for your token group",
        inline=False,
    )
    embed.add_field(
        name="\u200b",
        value="**Admin Commands**\n━━━━━━━━━━━━━━━━━━━━",
        inline=False,
    )
    embed.add_field(
        name="/dkp config",
        value=(
            "`/dkp config upload_channel #channel` — Set upload channel\n"
            "`/dkp config roster Inept` — Set CLM roster name\n"
            "`/dkp config admin_role @role` — Set admin role"
        ),
        inline=False,
    )
    embed.set_footer(text="Data is updated when a DKP manager uploads a CLM export.")
    await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    bot.tree.add_command(dkp_group)
