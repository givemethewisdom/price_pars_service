"""Base repository interface."""

import sqlite3
from abc import ABC
from pathlib import Path
from typing import Generic, TypeVar

from app.core.logger import app_logger

logger = app_logger.getChild("BaseRepo.sqlite")

ModelType = TypeVar("ModelType")


class BaseRepository(ABC, Generic[ModelType]):
    """Базовый репозиторий для SQLite."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """
        Получить соединение с БД.

        Returns:
            SQLite connection with Row factory
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Создать таблицы если не существуют."""
        # директория для БД
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Таблица prices
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS prices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticker TEXT NOT NULL,
                    price REAL NOT NULL,
                    estimated_delivery_price REAL,
                    timestamp INTEGER NOT NULL
                )
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_prices_ticker_timestamp
                ON prices (ticker, timestamp)
            """)

            # Таблица futures
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS futures (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    instrument_name TEXT NOT NULL,
                    last_price REAL NOT NULL,
                    index_price REAL NOT NULL,
                    mark_price REAL NOT NULL,
                    state TEXT NOT NULL,
                    stats_high REAL NOT NULL,
                    stats_low REAL NOT NULL,
                    stats_price_change REAL NOT NULL,
                    stats_volume REAL NOT NULL,
                    stats_volume_usd REAL NOT NULL,
                    open_interest INTEGER NOT NULL,
                    funding_8h REAL NOT NULL,
                    current_funding REAL NOT NULL,
                    min_price REAL NOT NULL,
                    max_price REAL NOT NULL,
                    settlement_price REAL NOT NULL,
                    best_ask_price REAL NOT NULL,
                    best_ask_amount REAL NOT NULL,
                    best_bid_price REAL NOT NULL,
                    best_bid_amount REAL NOT NULL,
                    estimated_delivery_price REAL NOT NULL,
                    interest_value REAL NOT NULL,
                    created_at REAL NOT NULL,
                    timestamp INTEGER NOT NULL
                )
            """)

            # Индексы для futures
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_futures_instrument_timestamp
                ON futures (instrument_name, timestamp)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_futures_timestamp
                ON futures (timestamp)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_futures_created_at
                ON futures (created_at)
            """)

            conn.commit()
            logger.debug("Database tables initialized (prices and futures)")
