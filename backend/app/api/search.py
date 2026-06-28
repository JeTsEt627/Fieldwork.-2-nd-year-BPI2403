"""Эндпоинты модуля индексации и поиска (BE-08, BE-09, BE-10)."""

from fastapi import APIRouter, Query

from app.api.dependencies import Cache, DbSession, EsService
from app.core.logging_config import get_logger
from app.schemas.search import (
    SearchHistoryItem,
    SearchHistoryResponse,
    SearchResponse,
)
from app.services import search_service

logger = get_logger(__name__)

router = APIRouter(tags=["Поиск"])


@router.get(
    "/search",
    response_model=SearchResponse,
    summary="Полнотекстовый поиск по документам",
    responses={
        200: {"description": "Результаты поиска (могут быть пустыми)"},
        400: {"description": "Некорректный поисковый запрос"},
        503: {"description": "Поисковый сервис временно недоступен"},
    },
)
async def search(
    session: DbSession,
    es_service: EsService,
    cache: Cache,
    q: str = Query(
        ...,
        min_length=1,
        max_length=1024,
        description="Поисковый запрос",
        examples=["машинное обучение"],
    ),
    page: int = Query(1, ge=1, description="Номер страницы (с 1)"),
    page_size: int = Query(10, ge=1, le=100, description="Результатов на странице"),
) -> SearchResponse:
    """Выполнить полнотекстовый поиск по проиндексированным документам.

    Реализует BE-08 (запрос ``multi_match`` к Elasticsearch), BE-09 (формат
    ответа) и BE-10 (кеширование повторных запросов в Redis). Дополнительно
    сохраняет запрос в историю и поддерживает пагинацию.

    Args:
        session: Сессия БД (внедряется).
        es_service: Сервис Elasticsearch (внедряется).
        cache: Сервис кеширования (внедряется).
        q: Текст поискового запроса.
        page: Номер страницы результатов.
        page_size: Количество результатов на странице.

    Returns:
        Результаты поиска в формате :class:`SearchResponse` (BE-09).

    Raises:
        SearchServiceError: Поисковый движок недоступен (приводит к HTTP 503).
    """
    result = await search_service.perform_search(
        session=session,
        es_service=es_service,
        cache_service=cache,
        query=q,
        page=page,
        page_size=page_size,
    )
    return SearchResponse(**result)


@router.get(
    "/search/history",
    response_model=SearchHistoryResponse,
    summary="История поисковых запросов",
)
async def search_history(
    session: DbSession,
    limit: int = Query(50, ge=1, le=200, description="Размер страницы"),
    offset: int = Query(0, ge=0, description="Смещение"),
) -> SearchHistoryResponse:
    """Вернуть историю поисковых запросов.

    Args:
        session: Сессия БД (внедряется).
        limit: Максимальное количество записей.
        offset: Смещение от начала выборки.

    Returns:
        Список записей истории и их общее количество.
    """
    items, total = await search_service.get_search_history(session, limit, offset)
    return SearchHistoryResponse(
        total=total,
        items=[SearchHistoryItem.model_validate(item) for item in items],
    )
