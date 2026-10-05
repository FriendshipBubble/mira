import random

import discord
import httpx
from discord import app_commands
from discord.ext import commands

from discord_utils import image_file_from_url


class VindEenVriendjeCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name='vindeenvriendje', description='Toon de lijst met afkortingen')
    async def vindeenvriendje(self, interaction: discord.Interaction):
        await interaction.response.defer()

        antwoord_opties = [
            'Ik kwam vandaag deze knapperd tegen!',
            'Ik zag zojuist dit beestje op Tinder. Zal ik links of rechts swipen?',
            'Zojuist was dit vriendje op bezoek.',
            'Dit is een foto van een van mijn beste vrienden.',
            'Heb je ooit een knapper huisdier dan deze gezien? Okay na mij dan, want ik ben natuurlijk de aller knapste!', # noqa: E501
            "The cuteness, it's too much... I'm in love!",
            'Vorige week had ik een date met deze hotstuff!',
            'Dit is een van mijn vriendjes!',
            'Ik kwam laatst dit vriendje tegen, maar we zijn vergeten telefoonnummers uit te wisselen. Weten jullie wie het baasje is zodat we een playdate kunnen organiseren?', # noqa: E501
            'Hier is een van mijn beste vrienden!',
            'Zojuist zag ik deze knapperd rondlopen! Was te verlegen om hallo te zeggen tho...',
            'Wie dit is? Mijn BFF natuurlijk!',
            '#vrienden #gezellig #bff #squadgoals',
        ]
        aantal_afbeeldingen = 1040
        random_nummer = random.randint(0, aantal_afbeeldingen)
        random_text = random.choice(antwoord_opties)
        img_url = f'https://static.friendshipbubble.nl/mira/pets/{random_nummer}.jpg'
        try:
            image_file = await image_file_from_url(img_url, filename='vriendje.jpg')
        except httpx.HTTPError:
            await interaction.followup.send('Ik kon de afbeelding niet ophalen.')
            return

        await interaction.followup.send(content=random_text, file=image_file)


async def setup(bot: commands.Bot):
    await bot.add_cog(VindEenVriendjeCog(bot))
