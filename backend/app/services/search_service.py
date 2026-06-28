"""Оркестрация поиска: кеш (BE-10) → Elasticsearch (BE-08) → история запросов.

Сначала проверяется кеш Redis; при промахе выполняется запрос к Elasticsearch,
результат кешируется, а сам факт запроса сохраняется в истории.
"""

import time

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging_config import get_logger
from app.models.search_history import SearchHistory
from app.services.cache import CacheService
from app.services.elasticsearch_service import ElasticsearchService

logger = get_logger(__name__)


async def perform_search(
    session: AsyncSession,
    es_service: ElasticsearchService,
    cache_service: CacheService,
    query: str,
    page: int,
    page_size: int,
) -> dict:
    """Выполнить поиск с кешированием и сохранением истории.

    Args:
        session: Сессия БД для записи истории.
        es_service: Сервис Elasticsearch.
        cache_service: Сервис кеширования.
        query: Поисковый запрос.
        page: Номер страницы (с 1).
        page_size: Количество результатов на странице.

    Returns:
        Словарь, совместимый со схемой ``SearchResponse``.
    """
    cache_key = cache_service.build_search_key(query, page, page_size)
    cached = await cache_service.get_json(cache_key)

    if cached is not None:
        logger.info("Кеш-хит для запроса %r (страница %d)", query, page)
        await _save_history(session, query, cached.get("total", 0), from_cache=True)
        return {
            "query": query,
            "page": page,
            "page_size": page_size,
            "from_cache": True,
            **cached,
        }

    started = time.perf_counter()
    es_result = await es_service.search(query=query, page=page, page_size=page_size)
    elapsed_ms = int((time.perf_counter() - started) * 1000)
    # Если Elasticsearch не вернул took, используем измеренное время.
    es_result["took_ms"] = es_result.get("took_ms") or elapsed_ms

    # Кешируем «полезную нагрузку» (без метаданных страницы и флага кеша).
    await cache_service.set_json(cache_key, es_result)

    await _save_history(session, query, es_result.get("total", 0), from_cache=False)

    return {
        "query": query,
        "page": page,
        "page_size": page_size,
        "from_cache": False,
        **es_result,
    }


async def _save_history(
    session: AsyncSession, query: str, results_count: int, from_cache: bool
) -> None:
    """Сохранить запись в историю поиска.

    Ошибки записи истории не должны влиять на основной ответ поиска, поэтому
    при сбое выполняется откат, а исключение логируется.

    Args:
        session: Сессия БД.
        query: Текст запроса.
        results_count: Количество найденных результатов.
        from_cache: Был ли ответ взят из кеша.
    """
    try:
        record = SearchHistory(
            query=query,
            results_count=results_count,
            from_cache=from_cache,
        )
        session.add(record)
        await session.commit()
    except Exception as exc:  # noqa: BLE001
        await session.rollback()
        logger.warning("Не удалось сохранить историю поиска: %s", exc)


async def get_search_history(
    session: AsyncSession, limit: int = 50, offset: int = 0
) -> tuple[list[SearchHistory], int]:
    """Вернуть историю поисковых запросов с пагинацией.

    Args:
        session: Сессия БД.
        limit: Максимальное количество записей.
        offset: Смещение от начала выборки.

    Returns:
        Кортеж ``(записи_истории, общее_количество)``.
    """
    total = await session.scalar(select(func.count()).select_from(SearchHistory))
    result = await session.execute(
        select(SearchHistory)
        .order_by(SearchHistory.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    items = list(result.scalars().all())
    return items, int(total or 0)
