"""redis cash"""

import json
import os
from typing import Optional, Any

import redis

from app.core.logger import app_logger

logger = app_logger.getChild("cash")


class RedisCache:
    def __init__(self):
        """Инициализация подключения к Redis используя те же настройки что и Celery (*for pipeline)"""
        # Если переменные не заданы - localhost (локальная разработка)
        self.host = os.getenv("REDIS_HOST", "localhost")
        self.port = int(os.getenv("REDIS_PORT", 6379))
        self.db = int(os.getenv("REDIS_DB", 1))

        try:
            self.client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=5,
                retry_on_timeout=True,
            )
            # Проверяем подключение
            self.client.ping()
        except redis.ConnectionError as e:
            logger.error("Failed to connect to Redis cache:%s", e)
            self.client = None

    def get(self, key: str) -> Optional[Any]:
        """Получить значение по ключу"""
        if not self.client:
            return None

        try:
            data = self.client.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.error("Redis get error for key %s,%s", key, e)
            return None

    def set(self, key: str, value: Any):
        """
        Установить значение БЕЗ TTL (вечное хранение)
        Перезаписывает существующее значение
        """
        if not self.client:
            return False

        try:
            self.client.set(key, json.dumps(value))
            logger.debug("Redis set: %s", key)
            return True
        except Exception as e:
            logger.error("Redis set error for key %s,%s", key, e)
            return False

    def set_with_ttl(self, key: str, value: Any, ttl_seconds: int):
        """Установка значения с TTL (пока не придумал применение)"""
        if not self.client:
            return False

        try:
            self.client.setex(key, ttl_seconds, json.dumps(value))
            logger.debug("Redis set: %s", key)
            return True
        except Exception as e:
            logger.error("Redis set error for key %s,%s", key, e)
            return False

    def set_if_not_exists(self, key: str, value: Any) -> bool:
        """
        Установить значение только если ключ не существует
        Возвращает True если ключ был установлен, False если ключ уже существовал
        """
        if not self.client:
            return False

        try:
            # SETNX = SET if Not eXists
            result = self.client.setnx(key, json.dumps(value))
            if result:
                logger.debug("Redis setnx (new): %s", key)
            else:
                logger.debug("Redis setnx (already exists): %s", key)
            return bool(result)
        except Exception as e:
            logger.error("Redis setnx error for key %s,%s", key, e)
            return False

    def update_if_exists(self, key: str, value: Any) -> bool:
        """
        Обновить значение только если ключ существует
        Возвращает True если ключ был обновлен, False если ключ не существовал
        """
        if not self.client or not self.exists(key):
            return False

        return self.set(key, value)

    def delete(self, key: str):
        """Удалить ключ"""
        if not self.client:
            return False

        try:
            result = self.client.delete(key)
            if result:
                logger.debug("Redis delete: %s", key)
            return result > 0
        except Exception as e:
            logger.error("Redis delete error for key %s,%s", key, e)
            return False

    def exists(self, key: str) -> bool:
        """Проверить существование ключа"""
        if not self.client:
            return False

        try:
            return bool(self.client.exists(key))
        except Exception as e:
            logger.error("Redis exists error for key %s,%s", key, e)
            return False

    def get_all_keys(self, pattern: str = "*") -> list:
        """Получить все ключи по паттерну"""
        if not self.client:
            return []

        try:
            return self.client.keys(pattern)
        except Exception as e:
            logger.error("Redis keys error for pattern %s,%s", pattern, e)
            return []

    def clear_all(self):
        """Очистить все ключи в текущей БД"""
        if not self.client:
            return False

        try:
            self.client.flushdb()
            logger.warning("Redis cache database cleared")
            return True
        except Exception as e:
            logger.error("Redis flushdb error: %s", e)
            return False


# Инициализация
cache = RedisCache()
