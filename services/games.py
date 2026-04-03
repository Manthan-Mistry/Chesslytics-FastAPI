import asyncio
import aiohttp

from core.http import fetch_json, validate_player
from core.utils import normalize, extract_opening
from services.archives import get_archives, filter_recent_archives


async def _fetch_archive_games(session: aiohttp.ClientSession, url: str) -> list[dict]:
    data = await fetch_json(session, url)
    return data.get("games", []) if data else []


async def fetch_recent_games(
    session: aiohttp.ClientSession,
    username: str,
    months: int,
) -> list[dict]:
    archives = await get_archives(session, username)
    archives = filter_recent_archives(archives, months)

    tasks = [_fetch_archive_games(session, url) for url in archives]
    results = await asyncio.gather(*tasks)

    return [game for batch in results if isinstance(batch, list) for game in batch]


async def get_validated_games(username: str, months: int) -> tuple[dict | None, list[dict]]:
    """
    Opens a single aiohttp session, validates the player, fetches games.
    Returns (player_data, games). player_data is None if not found.
    """
    async with aiohttp.ClientSession() as session:
        player = await validate_player(session, username)
        if not player:
            return None, []
        games = await fetch_recent_games(session, username, months)
    return player, games