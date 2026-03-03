# cogs/admin.py
import discord
from discord import app_commands
from discord.ext import commands
from parser.clm_parser import parse_clm_export, CLMParseError
from cogs.queries import dkp_group

config_group = app_commands.Group(name="config", description="Bot configuration", parent=dkp_group)


def is_admin(interaction: discord.Interaction) -> bool:
    admin_role_id = interaction.client.guild_configs.get(interaction.guild_id, {}).get("admin_role_id")
    if admin_role_id:
        return any(r.id == admin_role_id for r in interaction.user.roles)
    return interaction.user.guild_permissions.administrator


@config_group.command(name="upload_channel", description="Set the channel for DKP data uploads")
@app_commands.describe(channel="The channel to watch for CLM export uploads")
async def set_upload_channel(interaction: discord.Interaction, channel: discord.TextChannel):
    if not is_admin(interaction):
        await interaction.response.send_message("You don't have permission to do that.", ephemeral=True)
        return
    guild_id = interaction.guild_id
    if guild_id not in interaction.client.guild_configs:
        interaction.client.guild_configs[guild_id] = {}
    interaction.client.guild_configs[guild_id]["upload_channel_id"] = channel.id
    interaction.client.save_configs()
    await interaction.response.send_message(f"Upload channel set to {channel.mention}", ephemeral=True)


@config_group.command(name="roster", description="Set which CLM roster to use")
@app_commands.describe(name="The roster name from your CLM export")
async def set_roster(interaction: discord.Interaction, name: str):
    if not is_admin(interaction):
        await interaction.response.send_message("You don't have permission to do that.", ephemeral=True)
        return
    guild_id = interaction.guild_id
    if guild_id not in interaction.client.guild_configs:
        interaction.client.guild_configs[guild_id] = {}
    interaction.client.guild_configs[guild_id]["roster_name"] = name
    interaction.client.save_configs()
    await interaction.response.send_message(f"Roster set to **{name}**", ephemeral=True)


@config_group.command(name="admin_role", description="Set the admin role for bot management")
@app_commands.describe(role="The role that can manage the bot")
async def set_admin_role(interaction: discord.Interaction, role: discord.Role):
    if not is_admin(interaction):
        await interaction.response.send_message("You don't have permission to do that.", ephemeral=True)
        return
    guild_id = interaction.guild_id
    if guild_id not in interaction.client.guild_configs:
        interaction.client.guild_configs[guild_id] = {}
    interaction.client.guild_configs[guild_id]["admin_role_id"] = role.id
    interaction.client.save_configs()
    await interaction.response.send_message(f"Admin role set to {role.mention}", ephemeral=True)


class AdminCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

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
                roster_name = self.bot.guild_configs.get(guild_id, {}).get("roster_name")
                players, loot, history = parse_clm_export(raw_text, roster_name=roster_name)
                self.bot.ensure_store(guild_id).load_data(players, loot, history)
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
