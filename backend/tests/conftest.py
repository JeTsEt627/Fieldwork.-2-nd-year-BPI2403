"""Общие фикстуры для тестов бэкенда."""

import pytest
from httpx import ASGITransport, AsyncClient
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.services.elasticsearch_service import ElasticsearchService
from app.services.cache import CacheService


@pytest.fixture
def mock_es_service() -> ElasticsearchService:
    """Мок-сервис Elasticsearch."""
    service = MagicMock(spec=ElasticsearchService)
    service.ping = AsyncMock(return_value=True)
    service.ensure_index = AsyncMock()
    service.index_chunks = AsyncMock(return_value=5)
    service.search = AsyncMock(return_value={
        "total": 0,
        "took_ms": 1,
        "results": [],
    })
    service.delete_document = AsyncMock(return_value=0)
    return service


@pytest.fixture
def mock_cache_service() -> CacheService:
    """Мок-сервис кеширования."""
    service = MagicMock(spec=CacheService)
    service.ping = AsyncMock(return_value=False)
    service.enabled = False
    service.get_json = AsyncMock(return_value=None)
    service.set_json = AsyncMock()
    service.build_search_key = CacheService.build_search_key
    return service


@pytest.fixture
def mock_db_session() -> AsyncSession:
    """Мок-сессия базы данных."""
    session = MagicMock(spec=AsyncSession)
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.refresh = AsyncMock()
    session.get = AsyncMock(return_value=None)
    session.execute = AsyncMock()
    session.scalar = AsyncMock(return_value=0)
    session.delete = AsyncMock()
    return session


@pytest.fixture
async def async_client(mock_es_service, mock_cache_service, mock_db_session):
    """Асинхронный тестовый клиент FastAPI с заменёнными зависимостями."""
    from app.core.clients import get_cache_service, get_es_service
    from app.core.database import get_db_session

    app.dependency_overrides[get_db_session] = lambda: mock_db_session
    app.dependency_overrides[get_es_service] = lambda: mock_es_service
    app.dependency_overrides[get_cache_service] = lambda: mock_cache_service

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client

    app.dependency_overrides.clear()
