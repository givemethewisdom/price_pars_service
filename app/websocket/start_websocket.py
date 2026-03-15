"""Точка входа Websocket."""

import asyncio
from app.websocket.index_ws import IndexWebSocketManager

if __name__ == "__main__":
    manager = IndexWebSocketManager(testnet=False)
    asyncio.run(manager.start())  # работает вечно
