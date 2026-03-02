"""Global dependencies module."""

from app.repositories.futures_repo import FuturesRepository
from app.repositories.sqlite_repo import PriceRepository

# PriceRepository сам возьмет settings.DB_PATH из config
price_repo_dep = PriceRepository()  # Без параметров, используется settings.DB_PATH

# Если нужно явно указать путь:
# price_repo = PriceRepository("custom/path.db")

futures_repo = FuturesRepository()
