import sys
from pathlib import Path

from app.core.cash import cache
from app.core.logger import app_logger

sys.path.insert(0, str(Path(__file__).parent))

logger = app_logger.getChild("main")


async def get_futures_from_cache(instrument: str):
    """Получить данные фьючерса из кэша"""
    cache_key = f"futures:{instrument}"
    return cache.get(cache_key)


async def get_instruments_from_cache(ticker: str):
    """получить инструмент из кэша например btc_usd"""
    cache_key = f"ticker:{ticker}"
    return cache.get(cache_key)


if __name__ == "__main__":
    pass
