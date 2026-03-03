# DKPBot Design

Discord bot for Classic Loot Manager (CLM) — provides DKP standings, loot history, and related queries via Discord slash commands.

## Stack

- Python 3.11+
- discord.py v2.x (modern slash commands, Views for pagination)
- Railway for hosting
- Config via environment variables

## Architecture

```
CLM JSON export ──► DKP Manager uploads to hidden Discord channel
                              │
                              ▼
                    Bot detects .json attachment
                              │
                              ▼
                    Parses JSON → Player, Loot, History data
                              │
                              ▼
                    In-memory store (pickled to disk for restarts)
                              │
                              ▼
                    Guild members query via slash commands
```

## Data Flow

1. DKP manager exports from CLM in-game (`/clm export` → JSON)
2. Uploads JSON file to a hidden admin-only Discord channel
3. Bot auto-detects the upload, parses it, replaces previous data entirely (CLM exports are full snapshots)
4. Confirms in the channel: "Updated — X players, Y loot entries, Z history records"
5. Data persisted to pickle file so bot survives restarts without re-upload

## Project Structure

```
DKPBot/
├── bot.py              # Entry point, bot setup, event handlers
├── cogs/
│   ├── admin.py        # Upload handling, config commands
│   └── queries.py      # /dkp, /loot, /history, /item, /raidloot
├── parser/
│   └── clm_parser.py   # CLM JSON parsing and validation
├── models.py           # Player, LootEntry, HistoryEntry dataclasses
├── store.py            # In-memory data store + pickle persistence
├── display.py          # Embed formatting, pagination, class colors
├── requirements.txt
├── Procfile            # Railway: worker process
└── .env.example        # DISCORD_TOKEN, ADMIN_ROLE_ID
```

## Permissions

Two tiers:
- **Admin** (bot admin or configured DKP manager role): upload data, run `/config` commands
- **Everyone else**: query commands only (`/dkp`, `/loot`, `/history`, `/item`, `/raidloot`)

Upload channel visibility is handled by Discord's native channel permissions — no bot logic needed.

## Commands

### Admin

| Command | Description |
|---------|-------------|
| `/config upload_channel #channel` | Set channel where bot watches for uploads |
| `/config admin_role @role` | Set which role has admin access |

### Query

| Command | Options | Description |
|---------|---------|-------------|
| `/dkp` | `player`, `class` | DKP standings (yours, someone's, or by class) |
| `/loot` | `player` | Recent loot awards |
| `/history` | `player` | DKP transaction history |
| `/item` | `name` | Search loot records by item name |
| `/raidloot` | `date` | Loot from a specific raid (default: most recent) |

## Display

- Discord embeds with WoW class colors
- Class icons via emoji or text labels
- Pagination via discord.py `View` buttons for large result sets
- Footer showing last data update timestamp

## Data Model

Single roster, no multi-team support.

### Player
- Name, class, current DKP, lifetime gained, lifetime spent

### LootEntry
- Player, item ID, item name, DKP cost, timestamp

### HistoryEntry
- Player, DKP change amount, reason, awarded by, timestamp

## Configuration

Environment variables:
- `DISCORD_TOKEN` — bot token
- `ADMIN_ROLE_ID` — role with admin access (can also be set via `/config`)

Per-guild config stored alongside pickle data.

## Open Items

- **CLM JSON schema**: Need a real export to finalize the parser. Building with mock data until then.
- **Item links**: May link to Wowhead TBC Classic URLs for item lookups.
