# app/repositories/futures_repo.py
import sqlite3
from pathlib import Path
from typing import List, Optional, Dict, Any
from app.core.logger import app_logger
from app.core.config import settings

logger = app_logger.getChild("futures_repo")


class FuturesRepository:
    """Репозиторий для фьючерсов"""

    def __init__(self, db_path: str = None):
        self.db_path = db_path or settings.DB_PATH
        self._init_db()
        logger.info("Futures repository initialized with db: %s", self.db_path)

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Create futures table if it doesn't exist."""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS futures (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    instrument_name TEXT NOT NULL,
                    last_price REAL,
                    index_price REAL,
                    mark_price REAL,
                    timestamp INTEGER NOT NULL,
                    state TEXT,
                    stats_high REAL,
                    stats_low REAL,
                    stats_price_change REAL,
                    stats_volume REAL,
                    stats_volume_usd REAL,
                    open_interest REAL,
                    funding_8h REAL,
                    current_funding REAL,
                    min_price REAL,
                    max_price REAL,
                    settlement_price REAL,
                    best_ask_price REAL,
                    best_ask_amount REAL,
                    best_bid_price REAL,
                    best_bid_amount REAL,
                    estimated_delivery_price REAL,
                    interest_value REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_futures_instrument_timestamp
                ON futures (instrument_name, timestamp)
            """)

            conn.commit()
            logger.debug("Futures table initialized")

    def add_many_futures_repo(self, futures_list: List[Dict[str, Any]]) -> int:
        """
        Add multiple futures/perpetual records.
        наверное не нужен.

        Args:
            futures_list: List of dictionaries with futures data

        Returns:
            Number of inserted rows
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            data = []
            for item in futures_list:
                stats = item.get("stats", {})
                data.append(
                    (
                        item.get("instrument_name"),
                        item.get("last_price"),
                        item.get("index_price"),
                        item.get("mark_price"),
                        item.get("timestamp") // 1000,
                        item.get("state"),
                        stats.get("high"),
                        stats.get("low"),
                        stats.get("price_change"),
                        stats.get("volume"),
                        stats.get("volume_usd"),
                        item.get("open_interest"),
                        item.get("funding_8h"),
                        item.get("current_funding"),
                        item.get("min_price"),
                        item.get("max_price"),
                        item.get("settlement_price"),
                        item.get("best_ask_price"),
                        item.get("best_ask_amount"),
                        item.get("best_bid_price"),
                        item.get("best_bid_amount"),
                        item.get("estimated_delivery_price"),
                        item.get("interest_value"),
                    )
                )

            cursor.executemany(
                """
                INSERT INTO futures (
                    instrument_name, last_price, index_price, mark_price,
                    timestamp, state, stats_high, stats_low, stats_price_change,
                    stats_volume, stats_volume_usd, open_interest, funding_8h,
                    current_funding, min_price, max_price, settlement_price,
                    best_ask_price, best_ask_amount, best_bid_price,
                    best_bid_amount, estimated_delivery_price, interest_value
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                data,
            )

            conn.commit()
            return len(data)

    def get_latest_future_repo(self, instrument_name: str) -> Optional[Dict[str, Any]]:
        """Get latest record for a specific instrument."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM futures
                WHERE instrument_name = ?
                ORDER BY timestamp DESC
                LIMIT 1
            """,
                (instrument_name,),
            )

            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
