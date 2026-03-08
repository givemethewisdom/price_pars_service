import time

from app.core.cash import cache
from app.core.logger import app_logger

logger = app_logger.getChild("index_handler")


class IndexHandler:
    """Простой обработчик индексных цен"""

    def __init__(self):
        self.last_prices = {}

    async def handle(self, data: dict):
        """Обработка индексных цен."""
        index_name = data.get("index_name")
        price = data.get("price")
        timestamp = data.get("timestamp")

        if not index_name or not price:
            logger.warning(" Invalid index data: %s", data)
            return

        # Cash
        cache_key = f"index:{index_name}"
        cache.set(
            cache_key,
            {
                "price": price,
                "timestamp": timestamp // 1000 if timestamp else int(time.time()),
            },
        )
