import discord
from discord import app_commands
from discord.ext import commands


class AdminMessageCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(description='stuur een bericht in een kanaal')
    @app_commands.checks.has_permissions(manage_channels=True)
    @app_commands.describe(channel='Het kanaal waarin je het bericht wilt sturen', content='De inhoud van het bericht')
    async def message(self, interaction: discord.Interaction, channel: discord.TextChannel, content: str):
        await interaction.response.defer(ephemeral=True)

        try:
            await channel.send(content)
        except discord.DiscordException as exc:
            await interaction.edit_original_response(
                content=f'Er is een fout opgetreden bij het sturen van het bericht: {exc}'
            )
            return

        await interaction.edit_original_response(content=f'Bericht succesvol gestuurd in {channel.mention}')


async def setup(bot: commands.Bot):
    await bot.add_cog(AdminMessageCog(bot))
