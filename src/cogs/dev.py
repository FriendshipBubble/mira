import discord
from discord import app_commands
from discord.ext import commands


class OverCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _send_info(self, interaction: discord.Interaction):
        content = ''
        content += 'Ik ben gecreëerd en word onderhouden de devs van deze server!\n'
        content += 'Vraag gerust een van de devs over mij! (ze bijten niet)!\n'
        content += 'Je kan mijn werking op deze link vinden: <https://github.com/FriendshipBubble/mira>'
        await interaction.response.send_message(content, ephemeral=True)

    @app_commands.command(name="over", description="Informatie over de bot")
    async def over(self, interaction: discord.Interaction):
        await self._send_info(interaction)

    @app_commands.command(name="dev", description="Informatie over de bot")
    async def dev(self, interaction: discord.Interaction):
        await self._send_info(interaction)


async def setup(bot: commands.Bot):
    await bot.add_cog(OverCog(bot))
