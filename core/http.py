import aiohttp
from core.config import HEADERS, semaphore


async def fetch_json(session: aiohttp.ClientSession, url: str) -> dict | None:
    async with semaphore:
        async with session.get(url, headers=HEADERS) as response:
            if response.status == 200:
                return await response.json()
            return None


async def validate_player(session: aiohttp.ClientSession, username: str) -> dict | None:
    return await fetch_json(session, f"https://api.chess.com/pub/player/{username}")