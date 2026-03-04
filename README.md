# DKPBot

[![Python](https://img.shields.io/badge/python-3.12-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Lint](https://github.com/afrugalpenguin/dkpbot/actions/workflows/lint.yml/badge.svg)](https://github.com/afrugalpenguin/dkpbot/actions/workflows/lint.yml)
[![Downloads](https://img.shields.io/github/downloads/afrugalpenguin/dkpbot/total?logo=github)](https://github.com/afrugalpenguin/dkpbot/releases)

A Discord bot for [Classic Loot Manager](https://www.curseforge.com/wow/addons/classic-loot-manager) (CLM) DKP tracking. Upload your CLM JSON export and your guild can query DKP standings, loot history, and token competition right from Discord.

## Features

- `/dkp standings` — View DKP standings (all, by player, or by class)
- `/dkp loot` — Browse loot history
- `/dkp history` — View DKP transaction history
- `/dkp item` — Search loot by item name
- `/dkp raidloot` — View loot from a specific raid date
- `/dkp tokens` — See DKP standings for your TBC tier token group
- `/dkp help` — Show all commands

### Admin Commands

- `/dkp config upload_channel #channel` — Set the channel for CLM export uploads
- `/dkp config roster Name` — Set which CLM roster to use
- `/dkp config admin_role @role` — Set the bot admin role
- `/dkp config force_upload` — Bypass upload validation (one-time)

## Setup

### 1. Create a Discord Bot

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications)
2. Click **New Application**, give it a name, and click **Create**
3. Go to **Bot** in the sidebar
4. Click **Reset Token** and copy the token — you'll need this later
5. Under **Privileged Gateway Intents**, enable **Message Content Intent**
6. Go to **OAuth2** in the sidebar
7. Under **Scopes**, select `bot` and `applications.commands`
8. Under **Bot Permissions**, select:
   - Read Messages/View Channels
   - Send Messages
   - Embed Links
   - Attach Files
   - Read Message History
9. Copy the generated URL and open it in your browser to invite the bot to your server

### 2. Deploy to Railway

1. Fork this repo to your GitHub account
2. Go to [Railway](https://railway.com) and sign in with GitHub
3. Click **New Project** > **Deploy from GitHub Repo** > select your fork
4. Go to **Variables** and add:
   - `DISCORD_TOKEN` = your bot token from step 1
5. Railway will auto-deploy. Check the logs to confirm the bot is online

### 3. Configure the Bot

Once the bot is online in your Discord server:

1. Create a private channel for DKP uploads (e.g. `#dkp-upload`) — only your DKP manager needs access
2. Run `/dkp config upload_channel #dkp-upload`
3. Run `/dkp config roster YourRosterName` — this is the roster name from your CLM export (e.g. your guild name)
4. Upload your CLM JSON export to the upload channel

The bot will parse the export and confirm how many players, loot entries, and history records were loaded.

### 4. Export from CLM

In-game with Classic Loot Manager installed:

1. Open CLM settings
2. Use the export function to generate a JSON file
3. Upload the JSON file to your configured upload channel in Discord
4. The bot will automatically parse it and update the data

Re-upload whenever you want to refresh the data.

## Running Locally

```bash
git clone https://github.com/afrugalpenguin/dkpbot.git
cd dkpbot
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env
# Edit .env and add your bot token
python bot.py
```

## Running Tests

```bash
pip install pytest
pytest
```

## Upload Validation

The bot protects against bad uploads:
- Exports with **zero players** are rejected
- Exports with **less than half** the current player count are rejected (likely a bad export)
- Use `/dkp config force_upload` to bypass this check when intentional (e.g. roster restructure)

## Token Groups (TBC)

The `/dkp tokens` command shows DKP standings for players competing for the same tier tokens:

| Token | Classes |
|-------|---------|
| Fallen Hero | Hunter, Mage, Warlock |
| Fallen Champion | Paladin, Rogue, Shaman |
| Fallen Defender | Druid, Priest, Warrior |
