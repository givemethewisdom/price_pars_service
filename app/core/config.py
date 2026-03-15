"""Configuration settings for the application."""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    """Application settings."""

    # Deribit API
    deribit_api_url: str = os.getenv(
        "DERIBIT_API_URL", "https://test.deribit.com/api/v2"
    )
    # getenv возьмет либо из .env либо https://test.deribit.com/api/v2

    # Tickers to fetch
    tickers: list = None

    # Database
    DB_PATH: str = os.getenv(
        "DB_PATH", str(Path(__file__).parent.parent.parent / "data" / "prices.db")
    )
    CELERY_TICKERS: list = None

    # RabbitMQ
    RABBIT_USER: str = os.getenv("RABBIT_USER", "guest")
    RABBIT_PASS: str = os.getenv("RABBIT_PASS", "guest")
    RABBIT_HOST: str = os.getenv("RABBIT_HOST", "localhost")
    RABBIT_PORT: int = int(os.getenv("RABBIT_PORT", "5672"))
    RABBIT_PRICE_QUEUE: str = os.getenv("RABBIT_PRICE_QUEUE", "task_price")

    def __post_init__(self):
        """этот метод вызывается после создания объекта"""
        if self.tickers is None:
            self.tickers = ["btc_usd", "eth_usd"]

        if self.CELERY_TICKERS is None:
            self.CELERY_TICKERS = self.tickers  # по умолчанию те же


settings = Settings()
