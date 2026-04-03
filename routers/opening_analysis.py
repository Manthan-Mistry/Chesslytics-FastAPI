import polars as pl
from fastapi import APIRouter, HTTPException, Query

from core.utils import normalize, extract_opening
from services.games import get_validated_games

router = APIRouter()


def _build_df(games: list[dict]) -> pl.DataFrame:
    rows = [
        {
            "white_username": g.get("white", {}).get("username"),
            "black_username": g.get("black", {}).get("username"),
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


def _openings_by_color(df: pl.DataFrame, username_norm: str, color: str) -> tuple[list, list]:
    col_norm = f"{color}_norm"
    col_acc = f"{color}_accuracy"

    color_df = df.filter(pl.col(col_norm) == username_norm)
    if color_df.is_empty():
        return [], []

    most_played = (
        color_df.group_by("opening")
        .agg([pl.count().alias("games"), pl.mean(col_acc).alias("avg_accuracy")])
        .sort("games", descending=True)
        .head(3)
    )

    acc_df = color_df.filter(pl.col(col_acc).is_not_null())
    most_accurate = (
        acc_df.group_by("opening")
        .agg(pl.mean(col_acc).alias("avg_accuracy"))
        .sort("avg_accuracy", descending=True)
        .head(3)
        if not acc_df.is_empty() else pl.DataFrame()
    )

    return (
        [{row["opening"]: round(row["avg_accuracy"] or 0, 2)} for row in most_played.to_dicts()],
        [{row["opening"]: round(row["avg_accuracy"], 2)} for row in most_accurate.to_dicts()],
    )


@router.get("/player/{username}/openings-analysis-live")
async def opening_analysis_live(username: str, months: int = Query(6)):
    player, games = await get_validated_games(username, months)
    if player is None:
        raise HTTPException(status_code=404, detail="Player not found")

    df = _build_df(games)
    if df.is_empty():
        raise HTTPException(status_code=404, detail="No data found")

    username_norm = normalize(username)
    df = df.filter(
        (pl.col("white_norm") == username_norm) | (pl.col("black_norm") == username_norm)
    )
    if df.is_empty():
        raise HTTPException(status_code=404, detail="No data found")

    white_played, white_accurate = _openings_by_color(df, username_norm, "white")
    black_played, black_accurate = _openings_by_color(df, username_norm, "black")

    return {
        "username": username,
        "months": months,
        "analysis": {
            "white_most_played": white_played,
            "white_most_accurate": white_accurate,
            "black_most_played": black_played,
            "black_most_accurate": black_accurate,
        },
    }