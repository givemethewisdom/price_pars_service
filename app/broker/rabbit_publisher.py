"""Produces for rabbitmq"""

import json

from pika import ConnectionParameters, BlockingConnection
from pika.credentials import PlainCredentials

from app.core.config import settings
from app.core.logger import app_logger

logger = app_logger.getChild("rabbit_publisher")


class RabbitPublisher:
    """Producer сообщений в RabbitMQ"""

    def __init__(self, host="localhost", port=5672, queue=None):
        self.host = host
        self.port = port
        self.queue = queue
        self.credentials = PlainCredentials(settings.RABBIT_USER, settings.RABBIT_PASS)
        self.connection_params = ConnectionParameters(
            host=self.host,
            port=self.port,
            credentials=self.credentials,
            heartbeat=60,
            blocked_connection_timeout=30,
        )
        self.connection = None
        self.channel = None

    def connect(self):
        """Установка соединения"""
        try:
            self.connection = BlockingConnection(self.connection_params)
            self.channel = self.connection.channel()
            # Декларируем очередь (создаем если нет)
            self.channel.queue_declare(
                queue=self.queue
            )  # не сохраняю т.к. по логике в этом сервисе цены хранятся в БД
            # с durable=False соединение закрывается после этого блока. буду делать heartbeat
            logger.info(" Connected to RabbitMQ, queue:%s", self.queue)
        except Exception as e:
            logger.error(" Failed to connect to RabbitMQ: %s", e)

    def publish(self, message: dict):
        """Отправка сообщения"""
        if not self.channel:
            self.connect()

        try:
            self.channel.basic_publish(
                exchange="", routing_key=self.queue, body=json.dumps(message)
            )
            logger.debug(" Sent to RabbitMQ: %s", message)
        except Exception as e:
            logger.error(" Failed to publish:%s", e)
            # переподуключение при следжубющей отправке
            self.channel = None
            return False

    def close(self):
        """Закрытие соединения"""
        try:
            if self.channel and not self.channel.is_closed:
                self.channel.close()
            if self.connection and not self.connection.is_closed:
                self.connection.close()
            logger.info("RabbitMQ connection closed")
        except Exception as e:
            logger.error("Error closing connection:%s", e)
