import asyncio
from datetime import datetime
from dateutil.relativedelta import relativedelta
import aiohttp

from core.http import fetch_json


async def get_archives(session: aiohttp.ClientSession, username: str) -> list[str]:
    url = f"https://api.chess.com/pub/player/{username}/games/archives"
    data = await fetch_json(session, url)
    return data.get("archives", []) if data else []


def filter_recent_archives(archives: list[str], months_back: int) -> list[str]:
    if not archives:
        return []

    last_url = archives[-1]
    year, month = last_url.split("/")[-2:]
    latest = datetime(int(year), int(month), 1)
    cutoff = latest - relativedelta(months=months_back)

    return [
        url for url in archives
        if cutoff <= datetime(int(url.split("/")[-2]), int(url.split("/")[-1]), 1) <= latest
    ]