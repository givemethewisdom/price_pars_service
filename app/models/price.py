"""Price data models and SQLite storage."""

import time
from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional

from app.core.logger import app_logger

logger = app_logger.getChild("models")


@dataclass
class PriceData:
    """Price data model."""

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


@dataclass
class FuturesData:
    """Furures data model."""

    instrument_name: str
    last_price: float
    index_price: float
    mark_price: float
    state: str
    stats_high: float
    stats_low: float
    stats_price_change: float
    stats_volume: float
    stats_volume_usd: float
    open_interest: int
    funding_8h: float
    current_funding: float
    min_price: float
    max_price: float
    settlement_price: float
    best_ask_price: float
    best_ask_amount: float
    best_bid_price: float
    best_bid_amount: float
    estimated_delivery_price: float
    interest_value: float
    created_at: float
    timestamp: int = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = int(time.time())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
