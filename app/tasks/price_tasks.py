"""Celery tasks for fetching price data."""

import asyncio
from typing import List

from celery import shared_task

from app.core.logger import app_logger
from app.services.futures_serv import fetch_futures_serv
from app.services.price_serv import fetch_all_prices_serv

logger = app_logger.getChild("celery_tasks")


@shared_task(
    name="app.tasks.price_tasks.fetch_all_prices_task",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def fetch_all_prices_task(self, tickers: List[str]) -> dict:
    """
    Celery task to fetch and save prices.
    """

    # Запускаем асинхронную функцию в синхронном контексте
    # loop = asyncio.new_event_loop()
    # asyncio.set_event_loop(loop)
    # celery -A app.tasks.celery_app worker --loglevel=info -P threads
    # работает с asyncio.run флаг -P gevent должен работаьт для винды но не работает
    # ручной эвент луп с потоками пока не тестировал

    try:
        result = asyncio.run(fetch_all_prices_serv(tickers))

        prices_count = len(result.get("prices", []))
        errors_count = len(result.get("errors", []))

        return {
            "status": "success",
            "tickers": tickers,
            "prices_fetched": prices_count,
            "errors": errors_count,
            "timestamp": (
                result.get("prices", [{}])[0].get("timestamp")
                if result.get("prices")
                else None
            ),
        }

    except Exception as e:
        logger.error("Task failed: %s,", {e}, exc_info=True)

        # Повторная попытка
        self.retry(exc=e)


@shared_task(
    name="app.tasks.price_tasks.fetch_futures_task",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def fetch_futures_task(self, tickers: List[str]) -> dict:
    """selery task to fentch and save futures prices."""

    try:
        result = asyncio.run(fetch_futures_serv(tickers))

        prices_count = len(result.get("prices", []))
        errors_count = len(result.get("errors", []))

        return {
            "status": "success",
            "tickers": tickers,
            "prices_fetched": prices_count,
            "errors": errors_count,
            "timestamp": (
                result.get("prices", [{}])[0].get("timestamp")
                if result.get("prices")
                else None
            ),
        }

    except Exception as e:
        logger.error("Task failed: %s,", {e}, exc_info=True)

        # Повторная попытка
        self.retry(exc=e)
