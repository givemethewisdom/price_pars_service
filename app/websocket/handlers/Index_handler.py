import time

from app.broker.rabbit_publisher import RabbitPublisher
from app.core.cash import cache
from app.core.logger import app_logger

logger = app_logger.getChild("index_handler")


class IndexHandler:
    """Простой обработчик индексных цен"""

    def __init__(self):
        self.last_prices = {}

        # инициализация RABBITMQ
        self.rabbit = RabbitPublisher(queue="index_prices")
        self.rabbit.connect()

    async def handle(self, data: dict):
        """Обработка индексных цен."""
        index_name = data.get("index_name")
        price = data.get("price")
        timestamp = data.get("timestamp")

        if not index_name or not price:
            logger.warning(" Invalid index data: %s", data)
            return

        self.last_prices[index_name] = price
        logger.debug("Updated %s, in memory: %s", index_name, price)

        # сохранение Cash
        cache_key = f"index:{index_name}"
        cache.set(
            cache_key,
            {
                "price": price,
                "timestamp": timestamp // 1000 if timestamp else int(time.time()),
            },
        )

        rabbit_message = {
            "type": "index_price",
            "instrument": index_name,
            "price": price,
            "timestamp": (
                timestamp // 1000 if timestamp else int(time.time())
            ),  # будет чуть разное время с кэщем если timestamp нет в данных
        }

        # publish сам проверит соединение
        self.rabbit.publish(rabbit_message)
        logger.info(
            f" Index {index_name} sent to RabbitMQ: {price}"
        )  # захламляет консоль но можно контролировать брокер на время разработки

    def close(self):
        """Закрыть соединение с RabbitMQ"""
        self.rabbit.close()
