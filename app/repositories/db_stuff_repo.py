from app.core.logger import app_logger
from app.repositories.base import BaseRepository

logger = app_logger.getChild("db_stuff_repo")


class DatabaseCleaner(BaseRepository):
    """Простой очиститель базы данных"""

    def cleanup_table(self, table_name: str, keep_last: int = 100) -> int:
        """Оставляет последние N записей в таблице"""
        with self._get_connection() as conn:
            # Удаляет все, кроме последних N записей
            cursor = conn.execute(
                f"""
                DELETE FROM {table_name}
                WHERE id NOT IN (
                    SELECT id FROM {table_name}
                    ORDER BY timestamp DESC, id DESC
                    LIMIT ?
                )
            """,
                (keep_last,),
            )

            deleted = cursor.rowcount

            conn.commit()
            logger.info("Table %s: kept %s, deleted %s", table_name, keep_last, deleted)
            return deleted

    def cleanup_all(self, keep_last: int = 100) -> dict:
        """Очищает все таблицы в базе"""
        tables = ["prices", "futures"]
        results = {}

        for table in tables:
            try:
                results[table] = self.cleanup_table(table, keep_last)
            except Exception as e:
                logger.error("Error cleaning %s %s:", table, str(e))
                results[table] = -1

        return results
