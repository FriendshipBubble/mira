import logging
import pkgutil
from pathlib import Path

import discord
from discord.ext import commands

from config import (
    CLEAR_GLOBAL_COMMANDS,
    DISCORD_ADMIN_GUILD_ID,
    DISCORD_COMMAND_GUILD_ID,
    LOCAL_DEBUG,
    SYNC_COMMANDS,
)

logger = logging.getLogger(__name__)


class BubbleBot(commands.Bot):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(command_prefix=(), intents=intents)
        self._cogs_package = "cogs"
        self._cogs_path = Path(__file__).parent / "cogs"

    async def setup_hook(self):
        if not self._cogs_path.exists():
            logger.warning("No cogs directory found at %s; skipping cog loading", self._cogs_path)
            return

        for module in pkgutil.iter_modules([str(self._cogs_path)]):
            if module.name.startswith("_"):
                continue
            extension = f"{self._cogs_package}.{module.name}"
            try:
                await self.load_extension(extension)
                logger.info("Loaded cog: %s", extension)
            except Exception:
                logger.exception("Failed to load %s", extension)

        if not SYNC_COMMANDS:
            logger.info("Slash-command sync skipped (set SYNC_COMMANDS=true to sync)")
            return

        if LOCAL_DEBUG:
            guild_id = int(DISCORD_COMMAND_GUILD_ID or DISCORD_ADMIN_GUILD_ID)
            guild = discord.Object(id=guild_id)
            self.tree.copy_global_to(guild=guild)
            synced_commands = await self.tree.sync(guild=guild)
            logger.info("Synced %d slash command(s) to development guild %d", len(synced_commands), guild_id)
            logger.debug("Registered development slash commands: %s", [command.name for command in synced_commands])
            if CLEAR_GLOBAL_COMMANDS:
                previous_global_commands = self.tree.get_commands()
                self.tree.clear_commands(guild=None)
                await self.tree.sync()
                logger.warning(
                    "Removed %d global slash command(s); this also affects every guild using this Discord application",
                    len(previous_global_commands),
                )
            return

        synced_commands = await self.tree.sync()
        logger.info("Synced %d global slash command(s)", len(synced_commands))
