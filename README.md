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
DISCORD_REPORT_CHANNEL_ID=your_moderation_channel_id
# DISCORD_ALLOWED_ROLE_ID=your_allowed_role_id
```

Notes:
- Local runs default to `APP_ENV=local`, which enables verbose Discord and slash-command diagnostics. Set `APP_ENV=production` when running outside the local Compose configuration.
- Local runs skip slash-command syncing by default, preventing every reload from making another Discord API request. To register or update commands during development, temporarily set `SYNC_COMMANDS=true` in `.env` and restart once; local sync targets `DISCORD_COMMAND_GUILD_ID` (or falls back to `DISCORD_ADMIN_GUILD_ID`) for immediate updates. Set it back to `false` afterward. Production syncs global commands on startup.
- If local guild commands appear alongside older global commands, set both `SYNC_COMMANDS=true` and `CLEAR_GLOBAL_COMMANDS=true` for one startup to remove the global registrations. This is destructive for all servers using the same Discord application, so only do this if that application is not also serving production; set both back to `false` afterward. Discord may take time to stop displaying cached global commands.
- Keep `SYNC_COMMANDS=false` while iterating on non-command code. Discord rate limits are automatic; don't repeatedly restart just to retry a sync.
- `DISCORD_CHANNEL_ID` must be a numeric Discord channel ID.
- `DISCORD_TOKEN` is required and loaded automatically from `.env`.
- For OAuth, add the exact same callback URL (`DISCORD_REDIRECT_URI`) in your Discord Developer Portal app settings.
- `DISCORD_ADMIN_GUILD_ID` is required for protected `/message/` and `/say/` calls.
- `DISCORD_REPORT_CHANNEL_ID` is the channel where `/report` submissions are sent; the bot needs permission to view the channel and send messages/embed links there.
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
- `Slash-command sync skipped (set SYNC_COMMANDS=true to sync)` (default local mode)
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

## Host deployment with Docker Compose

The deployment workflow writes a self-contained `docker-compose.yml` into each
environment's `DEPLOY_PATH` on the self-hosted runner. It pins the image tag,
host port, and Compose project name (`mira-dev` or `mira-prod`) in that file.
The workflow regenerates it on every deployment, so edit the tracked
`docker-compose.prod.yml` template or the GitHub environment's `HOST_PORT`
variable rather than editing the generated file on the host.
For same-repository pull requests, the dev build and deployment both use the
PR merge commit, so template changes (including networks) can be tested on the
dev host before merging. This workflow skips fork PR deployments. Production
uses the merged commit after a push to `main`.
Because the dev environment executes PR Compose configurations on the host,
restrict branch write access, review workflow changes, and require a reviewer
for the GitHub `dev` environment. Look for `Generated Compose file:` to confirm
which host directory and template commit were used. The generated file is
named `docker-compose.yml`, not `docker-compose.prod.yml`.

Create a separate `.env` with the bot's credentials in each deploy directory
before the first deployment. The workflow requires this file but does not copy,
print, or overwrite it. From the appropriate `DEPLOY_PATH` on the host, use
ordinary commands without exporting image, port, or project variables:

```bash
docker compose pull
docker compose up -d
docker compose ps
docker compose logs -f
docker compose down
```

The checked-in `docker-compose.prod.yml` is the deployment template; the host
uses its generated `docker-compose.yml` by default. If the GHCR image is private,
the host's Docker installation must already be authenticated to pull it.
