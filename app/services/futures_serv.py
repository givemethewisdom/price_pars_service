import asyncio
import time

from app.api.deribit_client import DeribitClient
from app.core.cash import cache
from app.core.config import settings
from app.core.logger import app_logger
from app.services.dependencies import futures_repo
from app.exceptions import CustomException

logger = app_logger.getChild("futures_service")


async def fetch_futures_serv(tickers: list[str], base_url: str = None):
    """get futures info from Deribit API"""
    base_url = base_url or settings.deribit_api_url

    async with DeribitClient(base_url) as client:
        tasks = [client.get_ticker(ticker) for ticker in tickers]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        futures_dicts = []  # словари из API
        futures_objects = []  # объекты PriceData
        errors = []

        for ticker, result in zip(tickers, results):
            if isinstance(result, Exception):

                logger.error("Failed to fetch %s %s", ticker, result, exc_info=True)
                errors.append({"ticker": ticker, "error": str(result)})

            else:
                futures_dicts.append(result)

                # КЭШИРОВАНИЕ в Redis
                instrument = result["instrument_name"]
                cache_key = f"futures:{instrument}"
                cache.set(cache_key, result)

                from app.models.price import FuturesData

                timestamp_sec = (
                    result["timestamp"] // 1000
                    if "timestamp" in result
                    else int(time.time())
                )

                futures_obj = FuturesData(
                    instrument_name=result["instrument_name"],
                    last_price=result["last_price"],
                    index_price=result["index_price"],
                    mark_price=result["mark_price"],
                    state=result["state"],
                    stats_high=result["stats"]["high"],
                    stats_low=result["stats"]["low"],
                    stats_price_change=result["stats"]["price_change"],
                    stats_volume=result["stats"]["volume"],
                    stats_volume_usd=result["stats"]["volume_usd"],
                    open_interest=result["open_interest"],
                    funding_8h=result["funding_8h"],
                    current_funding=result["current_funding"],
                    min_price=result["min_price"],
                    max_price=result["max_price"],
                    settlement_price=result["settlement_price"],
                    best_ask_price=result["best_ask_price"],
                    best_ask_amount=result["best_ask_amount"],
                    best_bid_price=result["best_bid_price"],
                    best_bid_amount=result["best_bid_amount"],
                    estimated_delivery_price=result["estimated_delivery_price"],
                    interest_value=result["interest_value"],
                    created_at=float(timestamp_sec),  # <-- Добавлено обязательное поле!
                    timestamp=int(timestamp_sec),  # timestamp тоже в секундах
                )
                futures_objects.append(futures_obj)

        if errors:
            logger.warning("Some futures failed: %s", errors)

        try:
            if futures_objects:
                futures_repo.add_many_futures_repo(futures_dicts)

            return {
                "prices": futures_dicts,  # возвращаем словари для совместимости
                "errors": errors,
            }

        except CustomException:
            raise
        except Exception as e:
            logger.error("fetch_futures_serv error: %s", e, exc_info=True)
            raise CustomException(
                detail="server error", status_code=500, message="critical error"
            )


async def get_latest_future_serv(instrument_name: str):
    """get latest futures from DB"""
    res = futures_repo.get_latest_future_repo(instrument_name)
    return res
