from fastapi import FastAPI
from routers import (
    player_info,
    player_stats,
    player_performance,
    player_distribution,
    opening_analysis,
)

app = FastAPI(title="Chess Analytics API")

app.include_router(player_info.router)
app.include_router(player_stats.router)
app.include_router(player_performance.router)
app.include_router(player_distribution.router)
app.include_router(opening_analysis.router)


@app.get("/")
async def root():
    return {"message": "Chess Analytics API Running"}