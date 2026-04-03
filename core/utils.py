import re
from datetime import datetime, timezone


def normalize(username: str) -> str:
    return re.sub(r"[^a-z0-9_]", "", username.lower())


def to_iso_date(value: int | None) -> str | None:
    if value is None:
        return None
    if value > 10_000_000_000:
        value = value / 1000
    return datetime.fromtimestamp(value, tz=timezone.utc).isoformat()


def extract_opening(game: dict) -> str:
    try:
        pgn = game.get("pgn", "")
        if "ECOUrl" in pgn:
            opening = pgn.split("ECOUrl")[1].split("openings/")[1].split('"]')[0]
            return re.split(r"-(\d)", opening)[0]
    except Exception:
        pass
    return "Unknown"