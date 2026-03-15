"""Deribit API client."""

import asyncio

import aiohttp

from typing import Dict, Any
import time

from app.core.logger import app_logger

logger = app_logger.getChild("deribit_client")  # дочерний логгер


class DeribitClient:
    """Async client for Deribit API."""

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.timeout = aiohttp.ClientTimeout(
            total=30,  # общий таймаут на весь запрос
            connect=10,  # таймаут на подключение
            sock_read=20,  # таймаут на чтение данных
            sock_connect=10,  # таймаут на соединение сокета
        )
        self.session = None

    async def __aenter__(self):
        """Create session when entering context."""
        # при async with DeribitClient(url) as client: вызывается __aenter__ с сессией и при выходе __aexit__
        self.session = aiohttp.ClientSession(timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Close session when exiting context."""
        if self.session:
            await self.session.close()

    async def get_index_price(self, ticker: str) -> Dict[str, Any]:
        """
        Fetch current index price for a ticker.

        Args:
            ticker: Ticker name ('btc_usd', 'eth_usd')

        Returns:
            Dict with price data
        """

        url = f"{self.base_url}/public/get_index_price"
        params = {"index_name": ticker}
        try:
            async with asyncio.timeout(10):
                async with self.session.get(url, params=params) as response:

                    data = await response.json()
                    logger.debug("get_index_price data %s", data)

                    return {
                        "ticker": ticker,
                        "price": data["result"]["index_price"],
                        "estimated_delivery_price": data["result"][
                            "estimated_delivery_price"
                        ],
                        "timestamp": int(time.time()),
                        "raw_response": data,
                    }

        except asyncio.TimeoutError:
            logger.error(f"Timeout for {ticker}")

    async def get_ticker(self, instrument_name: str) -> Dict[str, Any]:
        """
        Retrieves the ticker (24-hour statistics) for a specific instrument.

        Args:
            instrument_name: Ticker name 'BTC-PERPETUAL', 'ETH-PERPETUAL','SOL-PERPETUAL'

        Returns:
            Dict ticker data
        """
        url = f"{self.base_url}/public/ticker"
        params = {"instrument_name": instrument_name}

        async with self.session.get(url, params=params) as response:
            data = await response.json()
            result = data.get("result")

        return result
