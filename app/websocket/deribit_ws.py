"""derivit websocket (стакан) слишком часто обновляется не могу
использовать из fastapi микросервиса. снепшоты делать не хочется.
"""

import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, List, Callable, Optional

import websockets

logger = logging.getLogger(__name__)


class ChannelType(Enum):
    """Типы каналов Deribit"""

    BOOK = "book"
    TICKER = "ticker"
    TRADES = "trades"
    INDEX = "deribit_price_index"
    PERPETUAL = "perpetual"
    PLATFORM = "platform.state"


@dataclass
class Subscription:
    """Подписка на канал"""

    channel: str
    callback: Callable
    instrument: Optional[str] = None
    interval: str = "100ms"


class DeribitWebSocket:
    """
    WebSocket клиент для Deribit API.
    Отдельный от HTTP клиента, использует другой протокол.
    """

    def __init__(self, testnet: bool = True):
        """
        Инициализация WebSocket клиента

        Args:
            testnet: Использовать testnet (True) или production (False)
        """
        self.testnet = testnet
        self.ws_url = (
            "wss://test.deribit.com/ws/api/v2"
            if testnet
            else "wss://www.deribit.com/ws/api/v2"
        )

        self.ws = None
        self.connection_id = None
        self.subscriptions: Dict[str, Subscription] = {}
        self.running = False
        self.message_id = 1
        self._reconnect_delay = 1

    async def connect(self):
        """Установка WebSocket соединения"""
        try:
            self.ws = await websockets.connect(
                self.ws_url, ping_interval=20, ping_timeout=20, close_timeout=10
            )
            self.running = True
            self.connection_id = f"ws_{datetime.now().timestamp()}"
            logger.info("WebSocket connected to %s", self.ws_url)

            # слушатель сообщений (async но без await из-за сложного контекста запуска??? РАЗОБРАТЬСЯ)
            asyncio.create_task(self._listen())

        except Exception as e:
            logger.error("WebSocket connection failed: %s", e)
            await self._reconnect()

    async def _listen(self):
        """Слушатель входящих сообщений"""
        while self.running and self.ws:
            try:
                message = await self.ws.recv()
                await self._handle_message(json.loads(message))

            except websockets.exceptions.ConnectionClosed:
                logger.warning("WebSocket connection closed")
                await self._reconnect()
                break
            except Exception as e:
                logger.error("Error handling message: %s,", e)

    async def _handle_message(self, message: dict):
        """Обработка входящих сообщений"""
        # Ответ на подписку/запрос
        if "id" in message:
            logger.debug(
                "Response to request %s:%s", message["id"], message.get("result")
            )

        # Подписка/обновление данных
        elif message.get("method") == "subscription":
            params = message.get("params", {})
            channel = params.get("channel")

            if channel and channel in self.subscriptions:
                # Вызываем колбэк подписчика
                subscription = self.subscriptions[channel]
                try:
                    await subscription.callback(params.get("data", {}))
                except Exception as e:
                    logger.error("Callback error for %s:%s", channel, e)

    async def subscribe(
        self,
        channel_type: ChannelType,
        instrument: str,
        callback: Callable,
        interval: str = "100ms",
    ):
        """
        Подписка на канал

        Args:
            channel_type: Тип канала (BOOK, TICKER, etc.)
            instrument: Название инструмента (BTC-PERPETUAL)
            callback: Функция-обработчик данных
            interval: Интервал обновлений (raw, 100ms, agg2)
        """
        if not self.ws or not self.running:
            logger.error("WebSocket not connected")
            return False

        # название канала
        if channel_type == ChannelType.INDEX:
            channel = f"{channel_type.value}.{instrument}"
        else:
            channel = f"{channel_type.value}.{instrument}.{interval}"

        # Сохраняем подписку
        self.subscriptions[channel] = Subscription(
            channel=channel, callback=callback, instrument=instrument, interval=interval
        )

        # Отправляем запрос на подписку
        msg_id = self._next_id()
        subscribe_msg = {
            "jsonrpc": "2.0",
            "method": "public/subscribe",
            "params": {"channels": [channel]},
            "id": msg_id,
        }

        try:
            await self.ws.send(json.dumps(subscribe_msg))
            logger.info("Subscribed to %s", channel)
            return True
        except Exception as e:
            logger.error("Subscribe failed for %s:%s", channel, e)
            return False

    async def subscribe_many(self, subscriptions: List[dict]):
        """
        Пакетная подписка на несколько каналов

        Args:
            subscriptions: Список подписок [{"channel_type":..., "instrument":..., "callback":..., "interval":...}]
        """
        channels = []

        for sub in subscriptions:
            channel_type = sub["channel_type"]
            instrument = sub["instrument"]
            interval = sub.get("interval", "100ms")

            if channel_type == ChannelType.INDEX:
                channel = f"{channel_type.value}.{instrument}"
            else:
                channel = f"{channel_type.value}.{instrument}.{interval}"

            channels.append(channel)
            self.subscriptions[channel] = Subscription(
                channel=channel,
                callback=sub["callback"],
                instrument=instrument,
                interval=interval,
            )

        # Пакетная подписка
        msg_id = self._next_id()
        subscribe_msg = {
            "jsonrpc": "2.0",
            "method": "public/subscribe",
            "params": {"channels": channels},
            "id": msg_id,
        }

        try:
            await self.ws.send(json.dumps(subscribe_msg))
            logger.info("Subscribed to %s", len(channels), channels)
            return True
        except Exception as e:
            logger.error("Batch subscribe failed: %s", e)
            return False

    async def unsubscribe(self, channel: str):
        """Отписка от канала"""
        if channel not in self.subscriptions:
            return

        msg_id = self._next_id()
        unsubscribe_msg = {
            "jsonrpc": "2.0",
            "method": "public/unsubscribe",
            "params": {"channels": [channel]},
            "id": msg_id,
        }

        try:
            await self.ws.send(json.dumps(unsubscribe_msg))
            del self.subscriptions[channel]
            logger.info("Unsubscribed from %s", channel)
        except Exception as e:
            logger.error("Unsubscribe failed: %s", e)

    async def _reconnect(self):
        """Переподключение при обрыве связи"""
        logger.info("Reconnecting in %s", self._reconnect_delay)
        await asyncio.sleep(self._reconnect_delay)

        # Exponential backoff
        self._reconnect_delay = min(self._reconnect_delay * 2, 60)

        try:
            await self.connect()
            # Восстанавливаем подписки
            if self.subscriptions:
                channels = list(self.subscriptions.keys())
                msg_id = self._next_id()
                subscribe_msg = {
                    "jsonrpc": "2.0",
                    "method": "public/subscribe",
                    "params": {"channels": channels},
                    "id": msg_id,
                }
                await self.ws.send(json.dumps(subscribe_msg))
                logger.info("Resubscribed to %s", len(channels), channels)
        except Exception as e:
            logger.error("Reconnection failed:%s", e)
            await self._reconnect()

    def _next_id(self) -> int:
        """Следующий ID сообщения"""
        self.message_id += 1
        return self.message_id

    async def close(self):
        """Закрытие соединения"""
        self.running = False
        if self.ws:
            await self.ws.close()
            logger.info("WebSocket connection closed")
