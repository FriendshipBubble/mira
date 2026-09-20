# Mira Bot Local Run Guide

This project runs a FastAPI app and a `discord.py` bot in the same process.

## 1) Prerequisites

- Python 3.10+
- A Discord bot token
- Bot invited to your server with:
  - `bot` scope
  - `applications.commands` scope
  - Send Messages permission in the target channel

## 2) Create and activate virtual environment

From the `mira` folder:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 3) Configure environment variables with .env

Create a `.env` file in the `mira` folder:

```bash
cp .env.example .env
```

Then edit `.env` and set values:

```dotenv
DISCORD_TOKEN=your_bot_token
DISCORD_CHANNEL_ID=your_channel_id
DISCORD_CLIENT_ID=your_discord_app_client_id
DISCORD_CLIENT_SECRET=your_discord_app_client_secret
DISCORD_REDIRECT_URI=http://127.0.0.1:8000/oauth/discord/callback
DISCORD_OAUTH_SCOPES=identify guilds guilds.members.read
DISCORD_ADMIN_GUILD_ID=your_server_guild_id
# DISCORD_ALLOWED_ROLE_ID=your_allowed_role_id
```

Notes:
- `DISCORD_CHANNEL_ID` must be a numeric Discord channel ID.
- `DISCORD_TOKEN` is required and loaded automatically from `.env`.
- For OAuth, add the exact same callback URL (`DISCORD_REDIRECT_URI`) in your Discord Developer Portal app settings.
- `DISCORD_ADMIN_GUILD_ID` is required for protected `/message/` and `/say/` calls.
- `DISCORD_OAUTH_SCOPES` should include `identify guilds guilds.members.read`.
- If `DISCORD_ALLOWED_ROLE_ID` is set, protected endpoints allow: admin OR member of that role.
- If `DISCORD_ALLOWED_ROLE_ID` is not set, protected endpoints allow: admin only.

## 4) Start locally

From the `mira` folder:

```bash
uvicorn main:app --app-dir src --reload
```

Expected startup logs include:
- `Loaded cog: cogs.ping`
- `Synced 1 slash command(s)`
- `<bot_name> has connected to Discord!`

## 5) Test the bot

### A) Discord slash command

In your server channel, run:

- `/ping`

Expected response:
- `Pong!`

### B) FastAPI endpoint triggers Discord message

Send a local API request:

```bash
curl -X POST http://127.0.0.1:8000/message/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message":"Hello from FastAPI"}'
```

You can also pass token as query param (helpful in docs/admin testing):

```bash
curl -X POST "http://127.0.0.1:8000/message/?access_token=YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message":"Hello from FastAPI"}'
```

Or use the alias endpoint:

```bash
curl -X POST http://127.0.0.1:8000/say/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message":"Hello from /say"}'
```

Expected result:
- HTTP `200` response with your JSON payload
- A message appears in the configured Discord channel

Access control behavior:
- The OAuth user must be in `DISCORD_ADMIN_GUILD_ID`.
- The OAuth user must be server owner/admin, or have `DISCORD_ALLOWED_ROLE_ID` if configured.

### C) Test Discord OAuth for API calls

1. Open this URL in your browser:

```text
http://127.0.0.1:8000/oauth/discord/login
```

2. Copy the `authorize_url` value from the JSON response and open it.
3. Approve the Discord consent screen.
4. You will be redirected to `/oauth/discord/callback` and receive token JSON.
  - This callback also sets an HTTP-only cookie used by protected endpoints.
5. Copy `access_token` and test API call:

```bash
curl "http://127.0.0.1:8000/oauth/discord/me?access_token=YOUR_ACCESS_TOKEN"
```

Expected result:
- Your Discord user profile JSON (`id`, `username`, etc.)

### D) Verify server admin authorization

Validate that the OAuth token belongs to an admin in your configured server:

```bash
curl http://127.0.0.1:8000/oauth/discord/check-admin \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

If you already completed `/oauth/discord/callback` in the same browser session,
you can call `/oauth/discord/check-admin` from FastAPI docs/admin UI without manually
adding `Authorization`, because the cookie is used automatically.

Expected result:
- `{"ok": true, ...}` with user and guild authorization details

## 6) Troubleshooting

- Slash command not visible:
  - Re-invite bot with `applications.commands` scope.
  - Wait a few seconds after startup sync.
- `Discord bot is not ready` or `503` from API:
  - Check token validity and bot login in logs.
- `Unable to access Discord channel ...`:
  - Verify `DISCORD_CHANNEL_ID` and channel permissions.
- `Discord OAuth is not configured`:
  - Set `DISCORD_CLIENT_ID` and `DISCORD_CLIENT_SECRET` in `.env`.
- `Authenticated user is not in the configured server`:
  - Ensure `DISCORD_ADMIN_GUILD_ID` matches the server where the user is a member.
- `Authenticated user is not an admin in configured server`:
  - Grant Administrator permission or use a server owner account for OAuth login.
- `Invalid OAuth state`:
  - Restart login flow from `/oauth/discord/login` and do not reuse old callback URLs.
- `Import ... could not be resolved` in editor:
  - Ensure VS Code uses `mira/.venv` interpreter.
