"""Настройка логирования приложения."""

import logging
import sys

from app.core.config import settings


def configure_logging() -> None:
    """Сконфигурировать корневой логгер для вывода в stdout.

    Уровень логирования зависит от флага ``debug`` в настройках. Формат
    включает время, уровень, имя логгера и сообщение.
    """
    level = logging.DEBUG if settings.debug else logging.INFO

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    # Избегаем дублирования обработчиков при повторной инициализации.
    root_logger.handlers.clear()
    root_logger.addHandler(handler)

    # Понижаем «шум» от сторонних библиотек.
    logging.getLogger("elastic_transport").setLevel(logging.WARNING)
    logging.getLogger("elasticsearch").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Вернуть именованный логгер.

    Args:
        name: Имя логгера (обычно ``__name__`` модуля).

    Returns:
        Экземпляр :class:`logging.Logger`.
    """
    return logging.getLogger(name)
