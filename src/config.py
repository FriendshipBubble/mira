import os

from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID", "1471581581746634959"))
DISCORD_CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")
DISCORD_CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET")
DISCORD_REDIRECT_URI = os.getenv("DISCORD_REDIRECT_URI", "http://127.0.0.1:8000/oauth/discord/callback")
DISCORD_OAUTH_SCOPES = os.getenv("DISCORD_OAUTH_SCOPES", "identify guilds guilds.members.read")
DISCORD_ADMIN_GUILD_ID = os.getenv("DISCORD_ADMIN_GUILD_ID")
DISCORD_ALLOWED_ROLE_ID = os.getenv("DISCORD_ALLOWED_ROLE_ID")
DISCORD_AUTH_COOKIE_NAME = os.getenv("DISCORD_AUTH_COOKIE_NAME", "discord_access_token")

# Shared secret for service-to-service calls (e.g. the frontend's background
# worker) that cannot complete an interactive Discord OAuth flow.
SERVICE_API_KEY = os.getenv("SERVICE_API_KEY")

ADMINISTRATOR_PERMISSION = 0x00000008

if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN is missing. Set it in your environment or .env file.")

if not DISCORD_ADMIN_GUILD_ID:
    raise RuntimeError("DISCORD_ADMIN_GUILD_ID is missing. Set it in your environment or .env file.")

if not SERVICE_API_KEY:
    raise RuntimeError("SERVICE_API_KEY is missing. Set it in your environment or .env file.")
