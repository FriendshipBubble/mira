import secrets
from typing import Optional
from urllib.parse import urlencode

import httpx
from fastapi import Cookie, Header, HTTPException, Response

from config import (
    ADMINISTRATOR_PERMISSION,
    DISCORD_ADMIN_GUILD_ID,
    DISCORD_AUTH_COOKIE_NAME,
    DISCORD_CLIENT_ID,
    DISCORD_CLIENT_SECRET,
    DISCORD_OAUTH_SCOPES,
    DISCORD_REDIRECT_URI,
    SERVICE_API_KEY,
)

oauth_states: set[str] = set()


async def verify_service_api_key(x_api_key: Optional[str] = Header(default=None)) -> dict:
    """Auth for machine callers (e.g. the frontend's background worker) that
    cannot complete an interactive Discord OAuth flow. Uses a static shared
    secret instead of a per-user token."""
    if not x_api_key or not secrets.compare_digest(x_api_key, SERVICE_API_KEY):
        raise HTTPException(status_code=401, detail="Missing or invalid X-API-Key header")
    return {"auth_type": "service"}


def require_discord_oauth_config():
    if not DISCORD_CLIENT_ID or not DISCORD_CLIENT_SECRET:
        raise HTTPException(
            status_code=500,
            detail=(
                "Discord OAuth is not configured. Set DISCORD_CLIENT_ID and "
                "DISCORD_CLIENT_SECRET in your .env file."
            ),
        )


def extract_bearer_token(authorization_header: Optional[str]) -> Optional[str]:
    if not authorization_header:
        return None
    parts = authorization_header.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    return parts[1].strip()


def resolve_token(
    access_token: Optional[str],
    authorization_header: Optional[str],
    cookie_token: Optional[str],
) -> Optional[str]:
    return access_token or extract_bearer_token(authorization_header) or cookie_token


async def build_discord_oauth_authorize_url() -> dict:
    require_discord_oauth_config()

    state = secrets.token_urlsafe(24)
    oauth_states.add(state)
    query = urlencode(
        {
            "client_id": DISCORD_CLIENT_ID,
            "redirect_uri": DISCORD_REDIRECT_URI,
            "response_type": "code",
            "scope": DISCORD_OAUTH_SCOPES,
            "state": state,
            "prompt": "consent",
        }
    )
    authorize_url = f"https://discord.com/api/oauth2/authorize?{query}"
    return {"authorize_url": authorize_url, "state": state}


async def exchange_discord_oauth_code(
    *,
    code: str,
    state: str,
    response: Response,
    error: Optional[str] = None,
) -> dict:
    require_discord_oauth_config()

    if error:
        raise HTTPException(status_code=400, detail=f"Discord OAuth error: {error}")
    if state not in oauth_states:
        raise HTTPException(status_code=400, detail="Invalid OAuth state")
    oauth_states.remove(state)

    payload = {
        "client_id": DISCORD_CLIENT_ID,
        "client_secret": DISCORD_CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": DISCORD_REDIRECT_URI,
    }

    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    async with httpx.AsyncClient(timeout=15) as client:
        discord_response = await client.post(
            "https://discord.com/api/oauth2/token",
            data=payload,
            headers=headers,
        )

    if discord_response.status_code >= 400:
        raise HTTPException(status_code=400, detail=f"Token exchange failed: {discord_response.text}")

    token_data = discord_response.json()
    access_token = token_data.get("access_token")
    if access_token:
        response.set_cookie(
            key=DISCORD_AUTH_COOKIE_NAME,
            value=access_token,
            httponly=True,
            samesite="lax",
            secure=False,
            max_age=int(token_data.get("expires_in", 3600)),
        )

    return token_data


async def get_discord_user_from_token(token: Optional[str]) -> dict:
    if not token:
        raise HTTPException(
            status_code=400,
            detail="Provide access_token query param or Authorization: Bearer <token>",
        )

    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.get(
            "https://discord.com/api/users/@me",
            headers={"Authorization": f"Bearer {token}"},
        )

    if response.status_code >= 400:
        raise HTTPException(status_code=400, detail=f"Discord API call failed: {response.text}")

    return response.json()


async def get_user_guilds_from_token(token: str) -> list[dict]:
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.get(
            "https://discord.com/api/users/@me/guilds",
            headers={"Authorization": f"Bearer {token}"},
        )

    if response.status_code >= 400:
        raise HTTPException(status_code=403, detail="Failed to verify guild permissions for user")

    return response.json()


def target_guild_entry(guilds: list[dict]) -> dict:
    target = next((guild for guild in guilds if guild.get("id") == DISCORD_ADMIN_GUILD_ID), None)
    if target is None:
        raise HTTPException(status_code=403, detail="Authenticated user is not in the configured server")
    return target


def is_admin_in_target_guild(guild_entry: dict) -> bool:
    is_owner = bool(guild_entry.get("owner", False))
    permissions_raw = guild_entry.get("permissions", "0")
    try:
        permissions_value = int(permissions_raw)
    except (TypeError, ValueError):
        permissions_value = 0

    is_admin = (permissions_value & ADMINISTRATOR_PERMISSION) == ADMINISTRATOR_PERMISSION
    return is_owner or is_admin


async def get_current_member_in_target_guild(token: str) -> dict:
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.get(
            f"https://discord.com/api/users/@me/guilds/{DISCORD_ADMIN_GUILD_ID}/member",
            headers={"Authorization": f"Bearer {token}"},
        )

    if response.status_code >= 400:
        raise HTTPException(
            status_code=403,
            detail=(
                "Failed to verify role membership. Ensure OAuth scope includes "
                "guilds.members.read and user is in the configured server."
            ),
        )

    return response.json()


def discord_authorization_wrapper(
    *,
    require_admin: bool = False,
    required_role_id: Optional[str] = None,
):
    async def dependency(
        access_token: Optional[str] = None,
        authorization: Optional[str] = Header(default=None),
        discord_access_token: Optional[str] = Cookie(default=None, alias=DISCORD_AUTH_COOKIE_NAME),
    ) -> dict:
        token = resolve_token(access_token, authorization, discord_access_token)
        if not token:
            raise HTTPException(
                status_code=401,
                detail=(
                    "Token missing. Provide one of: access_token query param, "
                    "Authorization: Bearer <token>, or login via /oauth/discord/callback "
                    "to set auth cookie."
                ),
            )

        user = await get_discord_user_from_token(token)
        guilds = await get_user_guilds_from_token(token)
        target = target_guild_entry(guilds)
        is_admin = is_admin_in_target_guild(target)

        has_required_role = False
        if required_role_id:
            member = await get_current_member_in_target_guild(token)
            roles = member.get("roles", [])
            has_required_role = required_role_id in roles

        if require_admin and required_role_id:
            if not (is_admin or has_required_role):
                raise HTTPException(
                    status_code=403,
                    detail="User must be an admin or have the required role in configured server",
                )
        elif require_admin and not is_admin:
            raise HTTPException(status_code=403, detail="Authenticated user is not an admin in configured server")
        elif required_role_id and not has_required_role:
            raise HTTPException(status_code=403, detail="Authenticated user does not have the required role")

        return {
            "token": token,
            "user": {
                "id": user.get("id"),
                "username": user.get("username"),
                "global_name": user.get("global_name"),
            },
            "guild": {
                "guild_id": DISCORD_ADMIN_GUILD_ID,
                "is_admin": is_admin,
                "required_role_id": required_role_id,
                "has_required_role": has_required_role,
            },
        }

    return dependency
