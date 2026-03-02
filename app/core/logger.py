"""Logging configuration for the application."""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler

# прапка для логов
log_dir = Path(__file__).parent.parent.parent / "logs"
log_dir.mkdir(exist_ok=True)


def setup_logger(name: str = "deribit_parser") -> logging.Logger:
    """
    Set up and configure a logger.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Предотвращаем добавление обработчиков несколько раз
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    # Формат логов
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(filename)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Консольный обработчик (вывод в терминал)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)  # В консоль только INFO и выше
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Файловый обработчик (все логи в файл)
    file_handler = RotatingFileHandler(
        log_dir / "app.log",
        maxBytes=10_485_760,  # 10MB
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)  # В файл пишем всё
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Обработчик для ошибок (отдельный файл)
    error_handler = RotatingFileHandler(
        log_dir / "error.log", maxBytes=10_485_760, backupCount=5, encoding="utf-8"
    )
    error_handler.setLevel(logging.ERROR)  # Только ошибки
    error_handler.setFormatter(formatter)
    logger.addHandler(error_handler)

    return logger


# глобальный логгер для приложения
app_logger = setup_logger("deribit_logger")
