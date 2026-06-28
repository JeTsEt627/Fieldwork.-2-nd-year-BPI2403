"""Кеширование частых поисковых запросов через Redis (BE-10).

Повторный одинаковый запрос обслуживается из кеша с временем жизни 5 минут.
Сервис устойчив к недоступности Redis: при ошибке подключения он просто не
кеширует, не нарушая работу поиска (требование имеет низкий приоритет).
"""

import hashlib
import json
from typing import Any

from redis.asyncio import Redis

from app.core.logging_config import get_logger

logger = get_logger(__name__)

# Префикс ключей кеша поиска.
SEARCH_KEY_PREFIX = "search"


class CacheService:
    """Обёртка над Redis для кеширования результатов поиска."""

    def __init__(self, client: Redis | None, ttl_seconds: int) -> None:
        """Инициализировать сервис кеширования.

        Args:
            client: Асинхронный клиент Redis либо ``None``, если кеш отключён.
            ttl_seconds: Время жизни записи кеша в секундах.
        """
        self._client = client
        self._ttl = ttl_seconds

    @property
    def enabled(self) -> bool:
        """Признак того, что кеширование активно."""
        return self._client is not None

    @staticmethod
    def build_search_key(query: str, page: int, page_size: int) -> str:
        """Сформировать ключ кеша для поискового запроса.

        Запрос нормализуется (обрезка пробелов, нижний регистр) и хешируется,
        чтобы одинаковые по смыслу запросы попадали в один ключ.

        Args:
            query: Поисковый запрос.
            page: Номер страницы.
            page_size: Размер страницы.

        Returns:
            Строковый ключ кеша.
        """
        normalized = query.strip().lower()
        digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:32]
        return f"{SEARCH_KEY_PREFIX}:{digest}:{page}:{page_size}"

    async def ping(self) -> bool:
        """Проверить доступность Redis.

        Returns:
            ``True``, если Redis отвечает, иначе ``False``.
        """
        if self._client is None:
            return False
        try:
            return await self._client.ping()
        except Exception:  # noqa: BLE001 - для health-check достаточно факта ошибки
            return False

    async def get_json(self, key: str) -> dict[str, Any] | None:
        """Получить и десериализовать значение из кеша.

        Args:
            key: Ключ кеша.

        Returns:
            Десериализованный словарь либо ``None``, если значения нет или
            кеш недоступен.
        """
        if self._client is None:
            return None
        try:
            raw = await self._client.get(key)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Не удалось прочитать кеш (%s): %s", key, exc)
            return None
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return None

    async def set_json(
        self, key: str, value: dict[str, Any], ttl_seconds: int | None = None
    ) -> None:
        """Сохранить значение в кеш в формате JSON.

        Args:
            key: Ключ кеша.
            value: Сериализуемый в JSON словарь.
            ttl_seconds: Время жизни записи; по умолчанию из настроек сервиса.
        """
        if self._client is None:
            return
        ttl = ttl_seconds if ttl_seconds is not None else self._ttl
        try:
            await self._client.set(
                key,
                json.dumps(value, ensure_ascii=False),
                ex=ttl,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("Не удалось записать кеш (%s): %s", key, exc)
