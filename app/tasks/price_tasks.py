"""Celery tasks for fetching price data."""

import asyncio
from typing import List, Optional
from celery import shared_task
from app.core.logger import app_logger

from app.api.deribit_client import DeribitClient
from app.services.dependencies import price_repo_dep, futures_repo
from app.services.futures_serv import get_ticker_serv
from app.services.price_serv import fetch_all_prices_serv
from app.core.config import settings

logger = app_logger.getChild("celery_tasks")


@shared_task(
    name="app.tasks.price_tasks.fetch_all_prices_task",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def fetch_all_prices_task(self, tickers: List[str]):
    """
    Celery task to fetch and save prices.
    """
    logger.info("Starting price fetch for tickers: %s", tickers)

    try:
        # Запускаем асинхронную функцию в синхронном контексте
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            result = loop.run_until_complete(fetch_all_prices_serv(tickers))

            # Логируем результат
            prices_count = len(result.get("prices", []))
            errors_count = len(result.get("errors", []))

            logger.info(
                "Task completed", extra={"prices": prices_count, "errors": errors_count}
            )

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

        finally:
            loop.close()

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
def fetch_futures_task(self, instrument_name: str):
    """celery task to fetch and save futures"""
    logger.info("starting info (mark) fentch for futures: %s", instrument_name)

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            res = loop.run_until_complete(get_ticker_serv(instrument_name))
            logger.info("Task completed", extra={"instrument_name": instrument_name})
            return {
                "status": "success",
                "futures": instrument_name,
            }
        # посмотреть где хранится время
        # "timestamp": result.get("prices", [{}])[0].get("timestamp") if result.get("prices") else None
        finally:
            loop.close()

    except Exception as e:
        logger.error("Task failed: %s,", {e}, exc_info=True)

        # Повторная попытка
        self.retry(exc=e)
