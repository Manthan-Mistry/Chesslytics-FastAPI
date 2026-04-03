import asyncio

HEADERS = {"User-Agent": "chess-analytics-app"}

CONCURRENT_REQUESTS = 5
semaphore = asyncio.Semaphore(CONCURRENT_REQUESTS)

# Result categories
WIN = ["win"]
LOSS = ["resigned", "checkmated", "timeout", "abandoned"]
DRAW = ["draw", "stalemate", "repetition", "insufficient", "agreed", "50move", "repetition", "timevsinsufficient"]