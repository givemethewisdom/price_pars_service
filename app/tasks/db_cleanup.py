from celery import shared_task

from app.core.config import settings
from app.core.logger import app_logger
from app.repositories.db_stuff_repo import DatabaseCleaner

logger = app_logger.getChild("db_cleanup")

db_path = settings.DB_PATH


@shared_task(
    name="app.tasks.db_cleanup.cleanup_database",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def cleanup_database(self):
    """Очистка базы данных - оставить последние 100 записей"""
    logger.info("Starting database cleanup task")
    try:
        cleaner = DatabaseCleaner(db_path)
        result = cleaner.cleanup_all(keep_last=100)
        logger.info("Cleanup completed: %s", result)
        return {"status": "success", "deleted": result}
    except Exception as e:
        logger.error("Cleanup failed: %s", str(e), exc_info=True)
        self.retry(exc=e)
