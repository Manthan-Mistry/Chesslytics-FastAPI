import requests
from fastapi import APIRouter, HTTPException

from core.config import HEADERS
from core.utils import to_iso_date

router = APIRouter()


def _get_player(username: str) -> dict | None:
    try:
        response = requests.get(
            f"https://api.chess.com/pub/player/{username}",
            headers=HEADERS,
        )
        if response.status_code != 200:
            return None
        data = response.json()
        return {
            "username": data.get("username"),
            "name": data.get("name"),
            "title": data.get("title"),
            "country": data.get("country"),
            "followers": data.get("followers"),
            "verified": data.get("verified"),
            "league": data.get("league"),
            "joined": to_iso_date(data.get("joined")),
            "last_online": to_iso_date(data.get("last_online")),
            "status": data.get("status"),
            "avatar": data.get("avatar"),
            "url": data.get("url"),
        }
    except Exception:
        return None


@router.get("/players/{username}")
def player_info(username: str):
    player = _get_player(username)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    return {"data": player}