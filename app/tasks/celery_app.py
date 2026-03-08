"""Celery application configuration."""

from celery import Celery
from celery.schedules import crontab

# Создаем экземпляр Celery
celery_app = Celery(
    "price_parser",
    broker="redis://localhost:6379/0",  # URL Redis для брокера
    backend="redis://localhost:6379/0",  # URL Redis для результатов
    include=["app.tasks.price_tasks", "app.tasks.db_cleanup"],  # где искать задачи
)

# Настройки Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=60,
    task_soft_time_limit=30,
)

# Настройка расписания для периодических задач
celery_app.conf.beat_schedule = {
    "fetch-prices-every-minute": {
        "task": "app.tasks.price_tasks.fetch_all_prices_task",
        "schedule": 60.0,  # каждые 60 секунд
        "args": (["btc_usd", "eth_usd"],),  # тикеры по умолчанию
    },
    "fetch-future-every-minute": {
        "task": "app.tasks.price_tasks.fetch_futures_task",
        "schedule": 60.0,  # каждые 60 секунд
        "args": (["BTC-PERPETUAL", "ETH-PERPETUAL"],),  # тикеры по умолчанию
    },
    "cleanup-database-daily": {
        "task": "app.tasks.db_cleanup.cleanup_database",
        "schedule": crontab(
            hour=3, minute=0
        ),  # каждый день в 3:00 (в моем случае не работает)
        # т.к. в 3 часа ночи я сплю и приложение отключено. нужно что-то придмать чтобы не удалять руками
    },
}
