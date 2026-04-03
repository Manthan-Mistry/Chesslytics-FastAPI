import re
import pandas as pd
from fastapi import APIRouter, HTTPException, Query

from core.config import WIN, LOSS, DRAW
from core.utils import normalize
from services.games import get_validated_games

router = APIRouter()


def _to_df(games: list[dict]) -> pd.DataFrame:
    rows = [
        {
            "white_username": g.get("white", {}).get("username"),
            "black_username": g.get("black", {}).get("username"),
            "white_rating": g.get("white", {}).get("rating"),
            "black_rating": g.get("black", {}).get("rating"),
            "white_result": g.get("white", {}).get("result"),
            "black_result": g.get("black", {}).get("result"),
            "game_time_class": g.get("time_class"),
        }
        for g in games
    ]
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df["white_norm"] = df["white_username"].astype(str).str.lower().str.replace(r"[^a-z0-9_]", "", regex=True)
    df["black_norm"] = df["black_username"].astype(str).str.lower().str.replace(r"[^a-z0-9_]", "", regex=True)
    return df


def _assign_player_cols(df: pd.DataFrame, player_norm: str) -> pd.DataFrame:
    df = df.copy()
    white = df["white_norm"] == player_norm
    black = df["black_norm"] == player_norm
    df["player_rating"] = None
    df["player_result"] = None
    df.loc[white, "player_rating"] = df.loc[white, "white_rating"]
    df.loc[black, "player_rating"] = df.loc[black, "black_rating"]
    df.loc[white, "player_result"] = df.loc[white, "white_result"]
    df.loc[black, "player_result"] = df.loc[black, "black_result"]
    df["player_rating"] = pd.to_numeric(df["player_rating"], errors="coerce")
    return df


def _avg_opp_rating(df: pd.DataFrame, player_norm: str) -> int | None:
    if df.empty:
        return None
    ratings = [
        row["black_rating"] if row["white_norm"] == player_norm else row["white_rating"]
        for _, row in df.iterrows()
    ]
    return round(sum(ratings) / len(ratings)) if ratings else None


def _best_win(df: pd.DataFrame, player_norm: str) -> dict | None:
    wins = df[df["player_result"].str.lower() == "win"].copy()
    if wins.empty:
        return None
    wins["opp_rating"] = None
    wins["opp_name"] = None
    for i, row in wins.iterrows():
        if row["white_norm"] == player_norm:
            wins.at[i, "opp_rating"] = row["black_rating"]
            wins.at[i, "opp_name"] = row["black_username"]
        else:
            wins.at[i, "opp_rating"] = row["white_rating"]
            wins.at[i, "opp_name"] = row["white_username"]
    idx = pd.to_numeric(wins["opp_rating"]).idxmax()
    return {"opponent_rating": int(wins.loc[idx, "opp_rating"]), "opponent_name": wins.loc[idx, "opp_name"]}


def _compute_metrics(df: pd.DataFrame, player_norm: str) -> dict | None:
    if df.empty:
        return None
    win_df = df[df["player_result"].isin(WIN)]
    draw_df = df[df["player_result"].isin(DRAW)]
    loss_df = df[df["player_result"].isin(LOSS)]
    return {
        "opponent_metrics": {
            "avg_opponent_rating": _avg_opp_rating(df, player_norm),
            "avg_opp_win": _avg_opp_rating(win_df, player_norm),
            "avg_opp_draw": _avg_opp_rating(draw_df, player_norm),
            "avg_opp_loss": _avg_opp_rating(loss_df, player_norm),
        },
        "best_ratings": {
            "best_rapid": int(df[df["game_time_class"] == "rapid"]["player_rating"].max()) if not df[df["game_time_class"] == "rapid"].empty else None,
            "best_blitz": int(df[df["game_time_class"] == "blitz"]["player_rating"].max()) if not df[df["game_time_class"] == "blitz"].empty else None,
            "best_bullet": int(df[df["game_time_class"] == "bullet"]["player_rating"].max()) if not df[df["game_time_class"] == "bullet"].empty else None,
        },
        "best_win": _best_win(df, player_norm),
    }


@router.get("/player-performance")
async def player_performance(player: str = Query(...), months: int = Query(6)):
    player_data, games = await get_validated_games(player, months)
    if player_data is None:
        raise HTTPException(status_code=400, detail="Player not found")

    df = _to_df(games)
    if df.empty:
        raise HTTPException(status_code=400, detail="No games found")

    player_norm = normalize(player)
    df = _assign_player_cols(df, player_norm)

    return {
        "player": player,
        "months": months,
        "performance": {
            "all": _compute_metrics(df, player_norm),
            "rapid": _compute_metrics(df[df["game_time_class"] == "rapid"], player_norm),
            "blitz": _compute_metrics(df[df["game_time_class"] == "blitz"], player_norm),
            "bullet": _compute_metrics(df[df["game_time_class"] == "bullet"], player_norm),
        },
    }