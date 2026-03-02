from app.api.deribit_client import DeribitClient
from app.core.config import settings
from app.core.logger import app_logger
from app.services.dependencies import futures_repo

logger = app_logger.getChild("futures_service")


async def get_ticker_serv(instrument_name: str, base_url: str = None):
    """get futures info from Deribit API"""
    base_url = base_url or settings.deribit_api_url
    async with DeribitClient(base_url) as client:
        res = await client.get_ticker(instrument_name)
        futures_repo.add_future_repo(res)
        return res


async def get_latest_future_serv(instrument_name: str):
    """get latest futures from DB"""
    res = futures_repo.get_latest_future_repo(instrument_name)
    return res
