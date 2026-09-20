import pkgutil
from pathlib import Path

import discord
from discord.ext import commands


class BubbleBot(commands.Bot):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(command_prefix=(), intents=intents)
        self._cogs_package = "cogs"
        self._cogs_path = Path(__file__).parent / "cogs"

    async def setup_hook(self):
        if not self._cogs_path.exists():
            print("No cogs directory found. Skipping cog loading.")
            return

        for module in pkgutil.iter_modules([str(self._cogs_path)]):
            if module.name.startswith("_"):
                continue
            extension = f"{self._cogs_package}.{module.name}"
            try:
                await self.load_extension(extension)
                print(f"Loaded cog: {extension}")
            except Exception as exc:
                print(f"Failed to load {extension}: {exc}")

        synced_commands = await self.tree.sync()
        print(f"Synced {len(synced_commands)} slash command(s)")
