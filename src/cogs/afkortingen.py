import discord
from discord import app_commands
from discord.ext import commands
import httpx

from discord_utils import image_file_from_url


class AfkortingenCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(description='Toon de lijst met afkortingen')
    async def afkortingen(self, interaction: discord.Interaction):
        img_url = 'https://static.friendshipbubble.nl/misc/afkortingen.jpg'
        await interaction.response.defer()

        try:
            image_file = await image_file_from_url(img_url, filename='afkortingen.jpg')
        except httpx.HTTPError:
            await interaction.followup.send('Ik kon de afbeelding niet ophalen.')
            return

        await interaction.followup.send(file=image_file)


async def setup(bot: commands.Bot):
    await bot.add_cog(AfkortingenCog(bot))
