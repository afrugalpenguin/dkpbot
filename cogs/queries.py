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
