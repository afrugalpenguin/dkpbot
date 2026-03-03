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


@bot.listen("on_guild_join")
async def on_guild_join(guild: discord.Guild):
    bot.ensure_store(guild.id)


if __name__ == "__main__":
    if not TOKEN:
        print("Error: DISCORD_TOKEN environment variable not set.")
        print("Copy .env.example to .env and add your bot token.")
        exit(1)
    bot.run(TOKEN)
