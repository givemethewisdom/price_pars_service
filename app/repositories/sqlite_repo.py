"""SQLite implementation of price repository.
all func-s with no commit.
"""

import sqlite3
from typing import List

from app.core.config import settings
from app.core.logger import app_logger
from app.exceptions import CustomException
from app.models.price import PriceData
from app.repositories.base import BaseRepository

logger = app_logger.getChild("repositories.sqlite_repo")


class PriceRepository(BaseRepository[PriceData]):
    """Репозиторий для цен."""

    def __init__(self, db_path: str = None):
        # Если путь не передан, берем из настроек
        if db_path is None:
            db_path = settings.DB_PATH

        super().__init__(db_path)
        logger.info("Price repository initialized with db: %s", db_path)

    def add_many_repo(self, prices: dict[PriceData]) -> int:
        """
        Пакетная вставка с контролем ошибок.
        """
        try:
            with self._get_connection() as conn:
                # зачем я передал список и собрал из него словарь?
                cursor = conn.cursor()
                data = [
                    (p.ticker, p.price, p.estimated_delivery_price, p.timestamp)
                    for p in prices
                ]
                cursor.executemany(
                    """
                    INSERT INTO prices (ticker, price, estimated_delivery_price, timestamp)
                    VALUES (?, ?, ?, ?)
                """,
                    data,
                )
                conn.commit()
                logger.info("Successfully saved all prices")
                return len(data)

        except sqlite3.Error as e:
            logger.error("Database error during bulk insert: %s", e)
            # Пробрасываем исключение - сервис решит, повторять или нет
            raise CustomException(
                detail=str(e), status_code=503, message="Database unavailable"
            )

    def get_latest_for_tickers_repo(self, tickers: List[str]) -> List[PriceData]:
        """
        Get latest price for specified tickers.

        Args:
            tickers: List of ticker symbols

        Returns:
            List of PriceData objects
        """
        if not tickers:
            return []

        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Создаем плейсхолдеры для IN запроса
            placeholders = ",".join(["?" for _ in tickers])

            cursor.execute(
                f"""
                SELECT p1.ticker, p1.price, p1.estimated_delivery_price, p1.timestamp
                FROM prices p1
                INNER JOIN (
                    SELECT ticker, MAX(timestamp) as max_timestamp
                    FROM prices
                    WHERE ticker IN ({placeholders})
                    GROUP BY ticker
                ) p2 ON p1.ticker = p2.ticker AND p1.timestamp = p2.max_timestamp
                ORDER BY p1.ticker
            """,
                tickers,
            )

            return [
                PriceData(
                    ticker=row["ticker"],
                    price=row["price"],
                    estimated_delivery_price=row["estimated_delivery_price"],
                    timestamp=row["timestamp"],
                )
                for row in cursor.fetchall()
            ]

    def get_by_ticker_repo(self, ticker: str, limit: int = 100) -> List[PriceData]:
        """
        Get prices by ticker.

        Args:
            ticker: Cryptocurrency ticker
            limit: Maximum number of records to return

        Returns:
            List of PriceData objects
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT ticker, price, estimated_delivery_price, timestamp
                FROM prices
                WHERE ticker = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """,
                (ticker, limit),
            )

            rows = cursor.fetchall()
            return [
                PriceData(
                    ticker=row["ticker"],
                    price=row["price"],
                    estimated_delivery_price=row["estimated_delivery_price"],
                    timestamp=row["timestamp"],
                )
                for row in rows
            ]

    def get_by_date_range_repo(
        self, ticker: str, start_time: int, end_time: int
    ) -> List[PriceData]:
        """
        Get prices within a time range.

        Args:
            ticker: Cryptocurrency ticker
            start_time: Start timestamp (inclusive)
            end_time: End timestamp (inclusive)

        Returns:
            List of PriceData objects
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT ticker, price, estimated_delivery_price, timestamp
                FROM prices
                WHERE ticker = ? AND timestamp BETWEEN ? AND ?
                ORDER BY timestamp ASC
            """,
                (ticker, start_time, end_time),
            )

            rows = cursor.fetchall()
            return [
                PriceData(
                    ticker=row["ticker"],
                    price=row["price"],
                    estimated_delivery_price=row["estimated_delivery_price"],
                    timestamp=row["timestamp"],
                )
                for row in rows
            ]

    def delete_old_repo(self, before_timestamp: int) -> int:
        """
        Delete records older than timestamp.

        Args:
            before_timestamp: Delete records with timestamp < this value

        Returns:
            Number of deleted rows
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM prices WHERE timestamp < ?", (before_timestamp,)
            )
            deleted = cursor.rowcount
            logger.info("Deleted %d old records", deleted)
            conn.commit()
            return deleted
