import asyncio
import logging

import discord

from bot_wrapper import BubbleBot
from commands import register_command
from config import APP_ENV, CHANNEL_ID, LOCAL_DEBUG, TOKEN

logging.basicConfig(
    level=logging.DEBUG if LOCAL_DEBUG else logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logging.getLogger().setLevel(logging.DEBUG if LOCAL_DEBUG else logging.INFO)
logging.getLogger("discord").setLevel(logging.DEBUG if LOCAL_DEBUG else logging.INFO)
logger = logging.getLogger(__name__)

intents = discord.Intents.default()
intents.message_content = True

bot = BubbleBot(intents=intents)
bot_task: asyncio.Task | None = None


@bot.event
async def on_ready():
    logger.info("%s has connected to Discord (environment=%s)", bot.user, APP_ENV)
    if LOCAL_DEBUG:
        logger.debug(
            "Discord connection ready: user_id=%s guild_count=%d latency=%.3fs",
            bot.user.id if bot.user else None,
            len(bot.guilds),
            bot.latency,
        )


@bot.listen()
async def on_app_command_completion(interaction: discord.Interaction, command: discord.app_commands.Command):
    if LOCAL_DEBUG:
        logger.debug(
            "Slash command completed: command=/%s user_id=%s guild_id=%s",
            command.qualified_name,
            interaction.user.id,
            interaction.guild_id,
        )


@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
    logger.error(
        "Slash command failed: command=/%s user_id=%s guild_id=%s",
        interaction.command.qualified_name if interaction.command else "unknown",
        interaction.user.id,
        interaction.guild_id,
        exc_info=(type(error), error, error.__traceback__),
    )


def bot_task_error() -> str | None:
    if bot_task is None or not bot_task.done() or bot_task.cancelled():
        return None
    exc = bot_task.exception()
    if exc is None:
        return "Discord bot stopped unexpectedly"
    return str(exc)


async def run_bot():
    try:
        await bot.start(TOKEN)
    except KeyboardInterrupt:
        await bot.close()
    except Exception:
        logger.exception("Discord bot failed to start")
        raise


async def start_bot_task():
    global bot_task
    if bot_task is None or bot_task.done():
        bot_task = asyncio.create_task(run_bot())


async def stop_bot_task():
    global bot_task
    if bot_task and not bot_task.done():
        await bot.close()
        bot_task.cancel()
        try:
            await bot_task
        except asyncio.CancelledError:
            pass


async def send_message(message_text: str):
    task_error = bot_task_error()
    if task_error:
        raise RuntimeError(f"Discord bot failed: {task_error}")

    if bot_task is None or bot_task.done():
        raise RuntimeError("Discord bot task is not running")

    if not bot.is_ready():
        try:
            await asyncio.wait_for(bot.wait_until_ready(), timeout=10)
        except asyncio.TimeoutError as exc:
            raise RuntimeError("Discord bot is not ready") from exc

    channel = bot.get_channel(CHANNEL_ID)
    if channel is None:
        try:
            channel = await bot.fetch_channel(CHANNEL_ID)
        except (discord.NotFound, discord.Forbidden, discord.HTTPException) as exc:
            raise RuntimeError(f"Unable to access Discord channel {CHANNEL_ID}") from exc

    if channel is None or not isinstance(channel, discord.abc.Messageable):
        raise RuntimeError(f"Discord channel {CHANNEL_ID} is not messageable")

    await channel.send(content=message_text)


@register_command(
    "send_message",
    description="Post a message to the configured Discord channel (CHANNEL_ID).",
    params={"message": "string, required - the text to send"},
)
async def _send_message_command(params: dict):
    message_text = params.get("message")
    if not message_text:
        raise ValueError("Missing required 'message' parameter")
    await send_message(message_text)
    return {"status": "sent"}
