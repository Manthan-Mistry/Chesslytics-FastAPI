import polars as pl
from fastapi import APIRouter, HTTPException, Query

from core.config import WIN, LOSS, DRAW
from core.utils import normalize, extract_opening
from services.games import get_validated_games

router = APIRouter()


def _build_df(games: list[dict]) -> pl.DataFrame:
    rows = [
        {
            "white_username": g.get("white", {}).get("username"),
            "black_username": g.get("black", {}).get("username"),
            "white_result": g.get("white", {}).get("result"),
            "black_result": g.get("black", {}).get("result"),
            "white_accuracy": g.get("accuracies", {}).get("white"),
            "black_accuracy": g.get("accuracies", {}).get("black"),
            "opening": extract_opening(g),
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


def _color_stats(df: pl.DataFrame, username_norm: str, color: str) -> dict:
    col_result = f"{color}_result"
    col_norm = f"{color}_norm"
    col_acc = f"{color}_accuracy"

    color_df = df.filter(pl.col(col_norm) == username_norm)
    total = color_df.height

    wins = color_df.filter(pl.col(col_result).is_in(WIN)).height
    losses = color_df.filter(pl.col(col_result).is_in(LOSS)).height
    draws = color_df.filter(pl.col(col_result).is_in(DRAW)).height

    acc = (
        color_df.filter(pl.col(col_acc).is_not_null())
        .select(pl.mean(col_acc))
        .item() or 0.0
    )

    return {
        "accuracy": round(acc, 2),
        "games": total,
        "wins": wins,
        "losses": losses,
        "draws": draws,
        "win_ratio": round(wins / total * 100, 2) if total else 0.0,
        "loss_ratio": round(losses / total * 100, 2) if total else 0.0,
        "draw_ratio": round(draws / total * 100, 2) if total else 0.0,
    }


@router.get("/players/{username}/stats")
async def player_stats(username: str, months: int = Query(6)):
    player, games = await get_validated_games(username, months)
    if player is None:
        raise HTTPException(status_code=404, detail="Player not found")

    df = _build_df(games)
    if df.is_empty():
        raise HTTPException(status_code=404, detail="No games found")

    username_norm = normalize(username)
    df = df.filter(
        (pl.col("white_norm") == username_norm) | (pl.col("black_norm") == username_norm)
    )

    return {
        "player": username,
        "months": months,
        "stats": {
            "total_games": df.height,
            "opening_lines": df.select(pl.col("opening").n_unique()).item(),
            "white": _color_stats(df, username_norm, "white"),
            "black": _color_stats(df, username_norm, "black"),
        },
    }