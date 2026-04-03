import polars as pl
from fastapi import APIRouter, HTTPException, Query

from core.config import WIN, LOSS, DRAW
from core.utils import normalize
from services.games import get_validated_games

router = APIRouter()

_OTHER = "other"


def _build_df(games: list[dict]) -> pl.DataFrame:
    rows = [
        {
            "white_username": g.get("white", {}).get("username"),
            "black_username": g.get("black", {}).get("username"),
            "white_result": g.get("white", {}).get("result"),
            "black_result": g.get("black", {}).get("result"),
        }
        for g in games if isinstance(g, dict)
    ]
    df = pl.DataFrame(rows)
    if df.is_empty():
        return df
    return df.with_columns([
        pl.col("white_username").str.to_lowercase().str.replace_all(r"[^a-z0-9_]", "").alias("white_norm"),
        pl.col("black_username").str.to_lowercase().str.replace_all(r"[^a-z0-9_]", "").alias("black_norm"),
    ])


def _distribution(df: pl.DataFrame, player_norm: str, category: str) -> dict:
    if category == "wins":
        trigger, reason_pool = WIN, LOSS
    elif category == "losses":
        trigger, reason_pool = LOSS, LOSS
    elif category == "draws":
        trigger, reason_pool = DRAW, DRAW
    else:
        raise ValueError(f"Unknown category: {category}")

    games = df.filter(
        ((pl.col("white_norm") == player_norm) & pl.col("white_result").is_in(trigger)) |
        ((pl.col("black_norm") == player_norm) & pl.col("black_result").is_in(trigger))
    )
    if games.is_empty():
        return {}

    if category in ("wins", "draws"):
        # reason comes from the opponent's result column
        games = games.with_columns(
            pl.when(pl.col("white_norm") == player_norm)
              .then(pl.col("black_result"))
              .otherwise(pl.col("white_result"))
              .alias("result_reason")
        )
    else:
        games = games.with_columns(
            pl.when(pl.col("white_norm") == player_norm)
              .then(pl.col("white_result"))
              .otherwise(pl.col("black_result"))
              .alias("result_reason")
        )

    games = games.with_columns(
        pl.when(pl.col("result_reason").is_in(reason_pool))
          .then(pl.col("result_reason"))
          .otherwise(pl.lit(_OTHER))
          .alias("result_reason")
    )

    total = games.height
    dist = (
        games.group_by("result_reason")
        .len()
        .with_columns(((pl.col("len") / total * 100).round(2)).alias("percentage"))
        .sort("percentage", descending=True)
        .select(["result_reason", "percentage"])
    )
    return {row["result_reason"]: row["percentage"] for row in dist.to_dicts()}


@router.get("/player/distribution/{username}")
async def player_distribution(username: str, months: int = Query(6)):
    player, games = await get_validated_games(username, months)
    if player is None:
        raise HTTPException(status_code=404, detail="Player not found")

    df = _build_df(games)
    if df.is_empty():
        raise HTTPException(status_code=404, detail="No games found")

    player_norm = normalize(username)
    return {
        "player": username,
        "months": months,
        "distribution": {
            "wins": _distribution(df, player_norm, "wins"),
            "draws": _distribution(df, player_norm, "draws"),
            "losses": _distribution(df, player_norm, "losses"),
        },
    }