import discord
from discord import Interaction
from discord import app_commands
from discord.ext import commands


class VraagAnnoniemCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name='vraag-annoniem', description='Stel een vraag anoniem in het huidige kanaal')
    @app_commands.describe(vraag='De vraag die je anoniem wilt stellen')
    async def vraag_annoniem(self, interaction: discord.Interaction, vraag: str):
        await interaction.response.send_message("Ik ga je vraag nu anoniem stellen.", ephemeral=True)
        try:
            if interaction.channel:
                await interaction.channel.send(f'Iemand vroeg: {vraag}')
        except Exception:
            await interaction.followup.send('Het is niet gelukt om de anonieme vraag te plaatsen.', ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(VraagAnnoniemCog(bot))
