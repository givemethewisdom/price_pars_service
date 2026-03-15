"""Price service for fetching and processing price data."""

import asyncio
from typing import List

from app.api.deribit_client import DeribitClient
from app.broker.rabbit_publisher import RabbitPublisher
from app.core.cash import cache
from app.core.config import settings
from app.core.logger import app_logger
from app.exceptions import CustomException
from app.models.price import PriceData
from app.services.dependencies import price_repo_dep

logger = app_logger.getChild("price_service")

# ОДИН ЭКЗЕМПЛЯР НА ВЕСЬ СЕРВИС
rabbit_publisher = RabbitPublisher(queue=settings.RABBIT_PRICE_QUEUE)

"""подключаемся один раз при старте а не каждый раз в функции
т.к. подключение даст доп. нагрузку на сборщик мусора и больше времени уйдет на
соединение и разрыв чем на отправку сообщения."""

rabbit_publisher.connect()


async def fetch_all_prices_serv(tickers: List[str], base_url: str = None) -> dict:
    """
    Fetch prices for multiple tickers concurrently, save it and push to rabbit queue.
    """

    rabbit_publisher = RabbitPublisher(queue=settings.RABBIT_PRICE_QUEUE)
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
                price_dicts.append(
                    result
                )  # result хранит полный формат ответа от Deribit
                logger.debug(f"price_dicts: {price_dicts}")

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

                rabbit_message = {
                    "type": "index_price",
                    "instrument": result["ticker"],
                    "price": result["price"],
                    "estimated_delivery_price": result["estimated_delivery_price"],
                    "timestamp": result["timestamp"],
                    "source": "price_pars_service",
                }

                rabbit_publisher.publish(rabbit_message)
                logger.info(" Sent %s to RabbitMQ", result["ticker"])

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


def close_rabbitmq():
    """Закрыть соединение с RabbitMQ при завершении"""
    # global rabbit_publisher
    if rabbit_publisher:
        try:
            rabbit_publisher.close()
            # лог закрытия в rabbit_publisher.close()
        except Exception as e:
            logger.error("Error closing RabbitMQ: %s", e)
