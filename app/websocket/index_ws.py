"""index price fetch for websocket."""

import asyncio

from app.core.cash import cache
from app.core.logger import app_logger
from app.websocket.deribit_ws import DeribitWebSocket, ChannelType
from app.websocket.handlers.Index_handler import IndexHandler

logger = app_logger.getChild("index_ws")


class IndexWebSocketManager:
    """Менеджер WebSocket подключений только для индексных цен."""

    def __init__(self, testnet: bool = True):
        """Dockstring for fkc flake."""
        self.ws_client = DeribitWebSocket(testnet=testnet)
        self.index_handler = IndexHandler()

        # Только индексы
        self.indices = ["btc_usd", "eth_usd", "sol_usd"]

    async def start(self):
        """Запуск WebSocket клиента."""
        logger.info(" Starting Index WebSocket Manager...")
        logger.info(" Tracking indices:%s", self.indices)

        # Подключаемся
        await self.ws_client.connect()
        await asyncio.sleep(1)

        # Подписываемся только на индексы
        for index in self.indices:
            await self.ws_client.subscribe(
                ChannelType.INDEX,
                index,
                self.index_handler.handle,
            )
            logger.info(" Subscribed to index:%s", index)

        logger.info("Waiting for index data...")

        # Держим соединение
        try:
            while True:
                await asyncio.sleep(30)  # проверка каждые 30 секунд
                # проверка особо не нужна т.к. вебсокет отправляет данные в FastAPi приложение через Rabbit
                # а сохраняет только свои с Celery для будущего функционала обработки. пока не буду убирать. Есть идеи
                self._show_status()

        except KeyboardInterrupt:
            logger.info("Stopping...")
            self.index_handler.close()  # соединение RabbitMQ
            await self.ws_client.close()

    def _show_status(self):
        """Показать статус (только индексы)."""
        for index in self.indices:
            # Берем данные из обработчика (последняя цена)
            price = self.index_handler.last_prices.get(index)
            if price:
                logger.info("Last %s,%s", index, price)
            else:
                # Если нет в обработчике, пробуем из Redis
                data = cache.get(f"index:{index}")
                if data:
                    logger.info(" Last %s, (from Redis):%s", index, data["price"])
                else:
                    logger.debug(" No data for %s", index)
