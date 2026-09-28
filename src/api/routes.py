from fastapi import APIRouter, Cookie, Depends, Header, HTTPException, Response
from pydantic import BaseModel

from api.auth import (
    build_discord_oauth_authorize_url,
    discord_authorization_wrapper,
    exchange_discord_oauth_code,
    get_discord_user_from_token,
    resolve_token,
    verify_service_api_key,
)
from bot_runtime import send_message
from commands import available_commands, describe_commands, get_command
from config import DISCORD_ALLOWED_ROLE_ID, DISCORD_AUTH_COOKIE_NAME

router = APIRouter()


class Item(BaseModel):
    message: str


class CommandRequest(BaseModel):
    params: dict = {}


@router.get("/")
async def hello():
    return {"message": "Hello"}


@router.get("/oauth/discord/login")
async def discord_oauth_login():
    return await build_discord_oauth_authorize_url()


@router.get("/oauth/discord/callback")
async def discord_oauth_callback(code: str, state: str, response: Response, error: str | None = None):
    return await exchange_discord_oauth_code(code=code, state=state, response=response, error=error)


@router.get("/oauth/discord/me")
async def discord_oauth_me(
    access_token: str | None = None,
    authorization: str | None = Header(default=None),
    discord_access_token: str | None = Cookie(default=None, alias=DISCORD_AUTH_COOKIE_NAME),
):
    token = resolve_token(access_token, authorization, discord_access_token)
    user = await get_discord_user_from_token(token)
    return user


@router.get("/oauth/discord/check-admin")
async def discord_oauth_check_admin(
    auth_context: dict = Depends(
        discord_authorization_wrapper(require_admin=True, required_role_id=DISCORD_ALLOWED_ROLE_ID)
    ),
):
    return {
        "ok": True,
        "user": auth_context["user"],
        "guild": auth_context["guild"],
    }


@router.post("/message/")
@router.post("/say/")
async def create_item(
    item: Item,
    auth_context: dict = Depends(
        discord_authorization_wrapper(require_admin=True, required_role_id=DISCORD_ALLOWED_ROLE_ID)
    ),
):
    _ = auth_context
    try:
        await send_message(item.message)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return item


@router.get("/commands")
async def list_commands(auth_context: dict = Depends(verify_service_api_key)):
    _ = auth_context
    return {"commands": describe_commands()}


@router.post("/commands/{command_name}")
async def run_command(
    command_name: str,
    payload: CommandRequest,
    auth_context: dict = Depends(verify_service_api_key),
):
    _ = auth_context
    try:
        handler = get_command(command_name)
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown command '{command_name}'. Available: {available_commands()}",
        )
    try:
        result = await handler(payload.params)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"command": command_name, "result": result}
