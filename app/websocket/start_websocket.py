"""Точка входа Websocket."""

# cd E:\proj_pyt\price_pars_service\price_pars_service
# python -m app.websocket.start_websocket
# надеюсь не добавлю в гит


import asyncio
from app.websocket.index_ws import IndexWebSocketManager

if __name__ == "__main__":
    manager = IndexWebSocketManager(testnet=False)
    asyncio.run(manager.start())  # работает вечно
