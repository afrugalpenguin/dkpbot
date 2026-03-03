# bot.py
import json
import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from store import GuildStore

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")


class DKPBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.messages = True
        intents.guilds = True
        super().__init__(command_prefix="!", intents=intents)
        self.guild_stores: dict[int, GuildStore] = {}
        self.guild_configs: dict[int, dict] = {}

    async def setup_hook(self):
        self.load_configs()
        await self.load_extension("cogs.queries")
        await self.load_extension("cogs.admin")

    async def on_ready(self):
        # Per-guild: clear stale, copy fresh, sync
        await self.tree.sync()
        for guild in self.guilds:
            self.tree.clear_commands(guild=guild)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
            # Ensure env-based config is applied to each guild
            self._apply_env_config(guild.id)
        print(f"DKPBot online as {self.user} (ID: {self.user.id})")
        print(f"Serving {len(self.guilds)} guild(s)")

    def _apply_env_config(self, guild_id: int):
        """Apply environment variable config as defaults (slash commands override)."""
        if guild_id not in self.guild_configs:
            self.guild_configs[guild_id] = {}
        cfg = self.guild_configs[guild_id]
        upload_channel = os.getenv("UPLOAD_CHANNEL_ID")
        roster_name = os.getenv("ROSTER_NAME")
        admin_role = os.getenv("ADMIN_ROLE_ID")
        if upload_channel and "upload_channel_id" not in cfg:
            cfg["upload_channel_id"] = int(upload_channel)
        if roster_name and "roster_name" not in cfg:
            cfg["roster_name"] = roster_name
        if admin_role and "admin_role_id" not in cfg:
            cfg["admin_role_id"] = int(admin_role)

    def load_configs(self):
        """Load configs from disk, falling back to env vars."""
        data_dir = os.getenv("DATA_DIR", "data")
        path = os.path.join(data_dir, "configs.json")
        if os.path.exists(path):
            with open(path) as f:
                raw = json.load(f)
                self.guild_configs = {int(k): v for k, v in raw.items()}

    def save_configs(self):
        data_dir = os.getenv("DATA_DIR", "data")
        os.makedirs(data_dir, exist_ok=True)
        path = os.path.join(data_dir, "configs.json")
        with open(path, "w") as f:
            json.dump({str(k): v for k, v in self.guild_configs.items()}, f, indent=2)

    def ensure_store(self, guild_id: int) -> GuildStore:
        if guild_id not in self.guild_stores:
            self.guild_stores[guild_id] = GuildStore()
        return self.guild_stores[guild_id]


bot = DKPBot()


@bot.listen("on_guild_join")
async def on_guild_join(guild: discord.Guild):
    bot.ensure_store(guild.id)


if __name__ == "__main__":
    if not TOKEN:
        print("Error: DISCORD_TOKEN environment variable not set.")
        print("Copy .env.example to .env and add your bot token.")
        exit(1)
    bot.run(TOKEN)
