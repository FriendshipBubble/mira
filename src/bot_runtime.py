import asyncio

import discord

from bot_wrapper import BubbleBot
from commands import register_command
from config import CHANNEL_ID, TOKEN

intents = discord.Intents.default()
intents.message_content = True

bot = BubbleBot(intents=intents)
bot_task: asyncio.Task | None = None


@bot.event
async def on_ready():
    print(f"{bot.user.name} has connected to Discord!")


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
    except Exception as exc:
        print(f"Discord bot failed to start: {exc}")
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
