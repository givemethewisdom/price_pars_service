"""Price data models and SQLite storage."""

import sqlite3
import time
from typing import Dict, List, Any, Optional
from pathlib import Path
from dataclasses import dataclass, asdict

from app.core.logger import app_logger
from app.core.config import settings

logger = app_logger.getChild("models")


@dataclass
class PriceData:
    """Price data model."""

    # нужно добавить датакласс для фьючерса

    ticker: str
    price: float
    estimated_delivery_price: Optional[float] = None
    timestamp: int = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = int(time.time())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
