"""Общие зависимости FastAPI для эндпоинтов.

Собирает воедино доступ к сессии БД, сервису Elasticsearch и сервису кеша,
оформляя их как ``Annotated``-типы для аккуратных сигнатур обработчиков.
"""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clients import get_cache_service, get_es_service
from app.core.database import get_db_session
from app.services.cache import CacheService
from app.services.elasticsearch_service import ElasticsearchService

# Сессия базы данных на время запроса.
DbSession = Annotated[AsyncSession, Depends(get_db_session)]

# Сервис полнотекстового поиска.
EsService = Annotated[ElasticsearchService, Depends(get_es_service)]

# Сервис кеширования результатов поиска.
Cache = Annotated[CacheService, Depends(get_cache_service)]
