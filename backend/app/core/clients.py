"""Управление жизненным циклом внешних клиентов (Elasticsearch, Redis).

Клиенты создаются один раз при старте приложения и переиспользуются во всех
запросах. Это эффективнее, чем открывать соединение на каждый запрос.
"""

from elasticsearch import AsyncElasticsearch
from redis.asyncio import Redis

from app.core.config import settings
from app.core.logging_config import get_logger
from app.services.cache import CacheService
from app.services.elasticsearch_service import ElasticsearchService

logger = get_logger(__name__)

# Глобальные синглтоны клиентов. Инициализируются в ``startup``.
_es_client: AsyncElasticsearch | None = None
_redis_client: Redis | None = None

_es_service: ElasticsearchService | None = None
_cache_service: CacheService | None = None


async def startup_clients() -> None:
    """Создать клиентов Elasticsearch и Redis и подготовить индекс.

    Вызывается при старте приложения. Ошибки подключения логируются, но не
    прерывают запуск: сервис может стартовать раньше, чем поднимутся внешние
    зависимости (например, в Docker Compose).
    """
    global _es_client, _redis_client, _es_service, _cache_service

    # --- Elasticsearch ---
    _es_client = AsyncElasticsearch(
        hosts=[settings.elasticsearch_url],
        request_timeout=30,
        max_retries=3,
        retry_on_timeout=True,
    )
    _es_service = ElasticsearchService(_es_client, settings.elasticsearch_index)
    try:
        await _es_service.ensure_index()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Не удалось подготовить индекс Elasticsearch при старте: %s", exc)

    # --- Redis ---
    if settings.cache_enabled:
        try:
            _redis_client = Redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
            await _redis_client.ping()
            logger.info("Подключение к Redis установлено")
        except Exception as exc:  # noqa: BLE001
            logger.warning("Redis недоступен, кеширование отключено: %s", exc)
            _redis_client = None
    _cache_service = CacheService(_redis_client, settings.cache_ttl_seconds)


async def shutdown_clients() -> None:
    """Корректно закрыть соединения клиентов при остановке приложения."""
    global _es_client, _redis_client

    if _es_client is not None:
        await _es_client.close()
        _es_client = None
        logger.info("Соединение с Elasticsearch закрыто")

    if _redis_client is not None:
        await _redis_client.aclose()
        _redis_client = None
        logger.info("Соединение с Redis закрыто")


def get_es_service() -> ElasticsearchService:
    """Вернуть сервис Elasticsearch (для использования как зависимость FastAPI).

    Returns:
        Инициализированный :class:`ElasticsearchService`.

    Raises:
        RuntimeError: Если клиент ещё не инициализирован.
    """
    if _es_service is None:
        raise RuntimeError("Elasticsearch-клиент не инициализирован")
    return _es_service


def get_cache_service() -> CacheService:
    """Вернуть сервис кеширования (для использования как зависимость FastAPI).

    Returns:
        Инициализированный :class:`CacheService`. Если Redis недоступен,
        сервис работает в режиме «без кеша».
    """
    if _cache_service is None:
        # Возвращаем «пустой» кеш, чтобы не падать, если старт ещё не прошёл.
        return CacheService(None, settings.cache_ttl_seconds)
    return _cache_service
