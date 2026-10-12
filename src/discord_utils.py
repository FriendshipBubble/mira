from io import BytesIO

import discord
import httpx


async def image_file_from_url(url: str, *, filename: str) -> discord.File:
    """Download an image URL and return it as a Discord file attachment."""
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.get(url)
        response.raise_for_status()

    return discord.File(BytesIO(response.content), filename=filename)
