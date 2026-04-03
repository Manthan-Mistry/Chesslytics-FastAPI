<div align="center">

```
 ██████╗██╗  ██╗███████╗███████╗███████╗
██╔════╝██║  ██║██╔════╝██╔════╝██╔════╝
██║     ███████║█████╗  ███████╗███████╗
██║     ██╔══██║██╔══╝  ╚════██║╚════██║
╚██████╗██║  ██║███████╗███████║███████║
 ╚═════╝╚═╝  ╚═╝╚══════╝╚══════╝╚══════╝
     ANALYTICS  ♟  API
```

**Real-time chess player analytics powered by the Chess.com Public API**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![aiohttp](https://img.shields.io/badge/aiohttp-async-2C5BB4?style=flat-square)](https://docs.aiohttp.org)
[![Polars](https://img.shields.io/badge/Polars-dataframes-CD792C?style=flat-square)](https://pola.rs)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)

</div>

---

## ♟ What is this?

**Chess Analytics API** is a high-performance, async REST API that fetches real-time game data from [Chess.com](https://chess.com) and turns it into deep, actionable player insights.

Want to know which openings a player crushes with? How they lose most often? Their best-ever win? This API answers all of that — fast.

---

## ✨ Features

| Feature | Description |
|---|---|
| 👤 **Player Info** | Profile, country, league, followers, join date |
| 📊 **Player Stats** | Win/loss/draw ratios & accuracy split by color (white & black) |
| 🏆 **Player Performance** | Best ratings, best win by opponent strength, avg opponent rating by result |
| 🥧 **Result Distribution** | *How* a player wins/loses/draws — checkmate, timeout, resignation, stalemate & more |
| 📖 **Opening Analysis** | Top 3 most-played & most-accurate openings per color |

All game endpoints support a configurable **lookback window** via the `months` query parameter.

---

## ⚡ Performance

Archive requests are fetched **in parallel** using `asyncio.gather()` behind a semaphore-controlled concurrency limit of 5 — keeping response times **under 5 seconds** even for high-volume players.

```
6 months of games · ~500 games
┌─────────────────────────────────┐
│  /stats              ~3.1s      │
│  /player-performance ~3.2s      │
│  /openings-analysis  ~3.2s      │
│  /distribution       ~4.1s      │
└─────────────────────────────────┘
```

---

## 🗂 Project Structure

```
chess_analytics/
│
├── main.py                        ← App entry point & router registration
│
├── core/
│   ├── config.py                  ← WIN / LOSS / DRAW constants, headers, semaphore
│   ├── http.py                    ← Async fetch helpers, player validation
│   └── utils.py                   ← normalize(), to_iso_date(), extract_opening()
│
├── services/
│   ├── archives.py                ← Archive fetching & date-range filtering
│   └── games.py                   ← Parallel game fetching, single session manager
│
└── routers/
    ├── player_info.py
    ├── player_stats.py
    ├── player_performance.py
    ├── player_distribution.py
    └── opening_analysis.py
```

---

## 🚀 Quick Start

**1. Clone the repo**
```bash
git clone https://github.com/your-username/chess-analytics-api.git
cd chess-analytics-api
```

**2. Install dependencies**
```bash
pip install fastapi uvicorn aiohttp requests polars pandas python-dateutil
```

**3. Run the server**
```bash
cd chess_analytics
uvicorn main:app --reload
```

**4. Open the interactive docs**
```
http://localhost:8000/docs
```

> Swagger UI is the fastest way to explore and test all endpoints.

---

## 📡 API Reference

### `GET /players/{username}`
Returns player profile information.

```bash
curl http://localhost:8000/players/hikaru
```

```json
{
  "data": {
    "username": "hikaru",
    "name": "Hikaru Nakamura",
    "followers": 1200000,
    "league": "Legend",
    "joined": "2010-04-01T00:00:00+00:00"
  }
}
```

---

### `GET /players/{username}/stats?months=6`
Win/loss/draw counts and ratios split by color.

```bash
curl http://localhost:8000/players/hikaru/stats?months=3
```

```json
{
  "player": "hikaru",
  "months": 3,
  "stats": {
    "total_games": 832,
    "opening_lines": 47,
    "white": {
      "accuracy": 91.4,
      "win_ratio": 68.2,
      "loss_ratio": 12.1,
      "draw_ratio": 19.7
    },
    "black": { "..." : "..." }
  }
}
```

---

### `GET /player-performance?player={username}&months=6`
Best ratings, opponent metrics, and best win — broken down by time control.

```bash
curl "http://localhost:8000/player-performance?player=hikaru&months=6"
```

```json
{
  "performance": {
    "blitz": {
      "best_ratings": { "best_blitz": 3842 },
      "best_win": { "opponent_rating": 3801, "opponent_name": "magnuscarlsen" },
      "opponent_metrics": { "avg_opponent_rating": 2940 }
    }
  }
}
```

---

### `GET /player/distribution/{username}?months=6`
Percentage breakdown of how a player wins, loses, and draws.

```bash
curl http://localhost:8000/player/distribution/hikaru
```

```json
{
  "distribution": {
    "wins":   { "checkmated": 61.3, "timeout": 27.8, "resigned": 10.9 },
    "losses": { "checkmated": 44.2, "timeout": 33.1, "resigned": 22.7 },
    "draws":  { "repetition": 55.0, "stalemate": 27.5, "50move": 17.5 }
  }
}
```

---

### `GET /player/{username}/openings-analysis-live?months=6`
Top 3 most-played and most-accurate openings per color.

```bash
curl http://localhost:8000/player/hikaru/openings-analysis-live
```

```json
{
  "analysis": {
    "white_most_played":   [{ "Kings-Indian-Attack": 91.2 }, { "... ": "..." }],
    "white_most_accurate": [{ "Ruy-Lopez":           94.7 }, { "...": "..." }],
    "black_most_played":   [{ "Sicilian-Defense":    90.1 }, { "...": "..." }],
    "black_most_accurate": [{ "Nimzo-Indian":        93.5 }, { "...": "..." }]
  }
}
```

---

## 🛠 Tech Stack

| Layer | Library |
|---|---|
| Web framework | [FastAPI](https://fastapi.tiangolo.com) |
| Async HTTP | [aiohttp](https://docs.aiohttp.org) |
| DataFrame (primary) | [Polars](https://pola.rs) |
| DataFrame (performance module) | [Pandas](https://pandas.pydata.org) |
| Date math | [python-dateutil](https://dateutil.readthedocs.io) |
| Server | [Uvicorn](https://www.uvicorn.org) |
| Data source | [Chess.com Public API](https://www.chess.com/news/view/published-api-documentation) |

---

## 📝 License

MIT — free to use, modify, and distribute.

---

<div align="center">

Made with ♟ and Python

</div>
