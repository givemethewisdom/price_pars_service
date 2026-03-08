"""Logging configuration for the application."""

import logging
import sys  # noqa: F401
from pathlib import Path
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler

# папка для логов
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

    # вывод в терминал
    console_handler = logging.StreamHandler(sys.stdout)  # noqa: F401
    console_handler.setLevel(logging.INFO)  # В консоль только INFO и выше
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # ЕЖЕДНЕВНЫЙ ФАЙЛОВЫЙ ОБРАБОТЧИК
    daily_handler = TimedRotatingFileHandler(
        filename=log_dir / "app.log",
        when="midnight",  # новая копия каждый день в полночь
        interval=1,  # каждый день
        backupCount=30,  # хранить 30 дней логов
        encoding="utf-8",
        utc=False,  # использовать локальное время
    )
    daily_handler.setLevel(logging.DEBUG)
    daily_handler.setFormatter(formatter)

    # Настройка суффикса для файлов
    daily_handler.suffix = "%Y-%m-%d"  # app.log.2026-03-08
    logger.addHandler(daily_handler)

    #  ОБРАБОТЧИК ДЛЯ ОШИБОК
    error_daily_handler = TimedRotatingFileHandler(
        filename=log_dir / "error.log",
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8",
    )
    error_daily_handler.setLevel(logging.ERROR)
    error_daily_handler.setFormatter(formatter)
    error_daily_handler.suffix = "%Y-%m-%d"
    logger.addHandler(error_daily_handler)

    # для защиты от слишком больших файлов в один день
    size_handler = RotatingFileHandler(
        log_dir / "app_size.log",
        maxBytes=50_000_000,  # 50MB
        backupCount=3,
        encoding="utf-8",
    )
    size_handler.setLevel(logging.DEBUG)
    size_handler.setFormatter(formatter)

    return logger


# глобальный логгер для приложения
app_logger = setup_logger("deribit_logger")
