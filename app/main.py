import asyncio
import sys
from pathlib import Path
from app.tasks.price_tasks import fetch_all_prices_task
from app.services.dependencies import price_repo_dep
from app.services.futures_serv import get_ticker_serv, get_latest_future_serv
from app.services.price_serv import fetch_all_prices_serv, get_newest_stock_price

# путь к проекту для импорта
sys.path.insert(0, str(Path(__file__).parent))

from app.core.logger import app_logger

logger = app_logger.getChild("main")


async def main():
    # Множественный fetch
    pass


if __name__ == "__main__":
    asyncio.run(main())
