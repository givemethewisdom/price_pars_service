"""Price service for fetching and processing price data."""

import asyncio
from typing import List

from app.api.deribit_client import DeribitClient
from app.core.cash import cache
from app.core.config import settings
from app.core.logger import app_logger
from app.exceptions import CustomException
from app.models.price import PriceData
from app.services.dependencies import price_repo_dep

logger = app_logger.getChild("price_service")


async def fetch_all_prices_serv(tickers: List[str], base_url: str = None) -> dict:
    """
    Fetch prices for multiple tickers concurrently and save it.
    """
    base_url = base_url or settings.deribit_api_url

    async with DeribitClient(base_url) as client:
        tasks = [client.get_index_price(ticker) for ticker in tickers]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        price_dicts = []  # словари из API
        price_objects = []  # объекты PriceData
        errors = []

        for ticker, result in zip(tickers, results):
            if isinstance(result, Exception):

                logger.error("Failed to fetch %s %s", ticker, result, exc_info=True)
                errors.append({"ticker": ticker, "error": str(result)})

            else:
                price_dicts.append(result)

                # cash
                ticker = result["ticker"]
                cache_key = f"ticker:{ticker}"
                cache.set(cache_key, result)

                # КОНВЕРТИРУЕМ В PriceData
                from app.models.price import PriceData

                price_obj = PriceData(
                    ticker=result["ticker"],
                    price=result["price"],
                    estimated_delivery_price=result["estimated_delivery_price"],
                    timestamp=result["timestamp"],
                )
                price_objects.append(price_obj)

        if errors:
            logger.warning("Some fetches failed: %s", errors)

        try:

            if price_objects:
                price_repo_dep.add_many_repo(price_objects)

            return {
                "prices": price_dicts,  # возвращаем словари для совместимости
                "errors": errors,
            }

        except CustomException:
            raise
        except Exception as e:
            logger.error("fetch_all_prices error: %s", e, exc_info=True)
            raise CustomException(
                detail="server error", status_code=500, message="critical error"
            )


async def get_newest_stock_price(tickers: list[str]) -> List[PriceData]:
    """returns newest stock price for tickers
    format:
     - ticker='btc_usd'
     - price=67017.56
     - estimated_delivery_price=67017.56
     - timestamp=1772349162
    """
    return price_repo_dep.get_latest_for_tickers_repo(tickers)
