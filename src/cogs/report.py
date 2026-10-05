import discord
from discord import app_commands
from discord.ext import commands

from config import DISCORD_REPORT_CHANNEL_ID


class ReportCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(description='Rapporteer een bericht')
    @app_commands.describe(
        omschrijving='Waarom je iets wilt rapporteren',
        persoon='Optioneel: de persoon die je wilt rapporteren',
        annoniem='Of je naam verborgen blijft voor moderators (Standaard: Ja)',
    )
    @app_commands.choices(
        annoniem=[
            app_commands.Choice(name='Ja', value='ja'),
            app_commands.Choice(name='Nee', value='nee'),
        ]
    )
    async def report(
        self,
        interaction: discord.Interaction,
        omschrijving: str,
        persoon: discord.Member | None = None,
        annoniem: str = 'ja',
    ):
        await interaction.response.defer(ephemeral=True)

        if not DISCORD_REPORT_CHANNEL_ID:
            await interaction.edit_original_response(
                content='Rapporteren is nog niet ingesteld: DISCORD_REPORT_CHANNEL_ID ontbreekt.'
            )
            return

        try:
            report_channel_id = int(DISCORD_REPORT_CHANNEL_ID)
        except ValueError:
            await interaction.edit_original_response(
                content='Rapporteren is niet goed ingesteld: DISCORD_REPORT_CHANNEL_ID moet een kanaal-ID zijn.'
            )
            return

        report_channel = self.bot.get_channel(report_channel_id)
        if report_channel is None:
            try:
                report_channel = await self.bot.fetch_channel(report_channel_id)
            except discord.DiscordException:
                await interaction.edit_original_response(
                    content='Ik kan het ingestelde rapportagekanaal niet openen.'
                )
                return

        if not isinstance(report_channel, discord.abc.Messageable):
            await interaction.edit_original_response(
                content='Het ingestelde rapportagekanaal kan geen berichten ontvangen.'
            )
            return

        embed = discord.Embed(title='Er is een nieuw report gestuurd', color=discord.Color.red())
        persoon_omschrijving = f'{persoon.mention} (`{persoon.id}`)' if persoon else 'Niet opgegeven'
        embed.add_field(name='Gerapporteerde persoon', value=persoon_omschrijving, inline=False)
        embed.add_field(name='Omschrijving', value=omschrijving, inline=False)
        embed.add_field(
            name='Gemeld door',
            value='Anoniem' if annoniem == 'ja' else f'{interaction.user.mention} (`{interaction.user.id}`)',
            inline=False,
        )
        if interaction.guild:
            embed.add_field(name='Server', value=interaction.guild.name, inline=True)
        if interaction.channel:
            embed.add_field(name='Kanaal', value=interaction.channel.mention, inline=True)

        try:
            await report_channel.send(embed=embed)
        except discord.DiscordException:
            await interaction.edit_original_response(
                content='Ik kon de rapportage niet versturen. Controleer mijn kanaalrechten.'
            )
            return

        await interaction.edit_original_response(content='Je rapport is verstuurd naar de moderators.')


async def setup(bot: commands.Bot):
    await bot.add_cog(ReportCog(bot))
