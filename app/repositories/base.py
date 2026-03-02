"""Base repository interface."""

import sqlite3
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional, Generic, TypeVar

from app.core.logger import app_logger
from app.models.price import PriceData

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
                CREATE INDEX IF NOT EXISTS idx_ticker_timestamp
                ON prices (ticker, timestamp)
            """)
            conn.commit()
            logger.debug("Database tables initialized")
