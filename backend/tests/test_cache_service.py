"""Юнит-тесты сервиса кеширования Redis (BE-10)."""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.services.cache import CacheService


@pytest.fixture
def redis_client():
    client = MagicMock()
    client.ping = AsyncMock(return_value=True)
    client.get = AsyncMock(return_value=None)
    client.set = AsyncMock()
    return client


@pytest.fixture
def cache_service(redis_client) -> CacheService:
    return CacheService(redis_client, ttl_seconds=300)


@pytest.fixture
def cache_service_disabled() -> CacheService:
    return CacheService(None, ttl_seconds=300)


class TestCacheServiceEnabled:
    def test_enabled_when_client_provided(self, cache_service):
        assert cache_service.enabled is True

    def test_disabled_when_no_client(self, cache_service_disabled):
        assert cache_service_disabled.enabled is False

    async def test_ping_returns_true(self, cache_service):
        assert await cache_service.ping() is True

    async def test_ping_disabled_returns_false(self, cache_service_disabled):
        assert await cache_service_disabled.ping() is False

    async def test_get_json_returns_none_for_missing_key(self, cache_service, redis_client):
        redis_client.get.return_value = None
        result = await cache_service.get_json("key")
        assert result is None

    async def test_get_json_returns_parsed_value(self, cache_service, redis_client):
        data = {"total": 5, "results": []}
        redis_client.get.return_value = json.dumps(data)
        result = await cache_service.get_json("key")
        assert result == data

    async def test_get_json_returns_none_on_redis_error(self, cache_service, redis_client):
        redis_client.get.side_effect = Exception("connection lost")
        result = await cache_service.get_json("key")
        assert result is None

    async def test_get_json_returns_none_on_invalid_json(self, cache_service, redis_client):
        redis_client.get.return_value = "not json {"
        result = await cache_service.get_json("key")
        assert result is None

    async def test_set_json_calls_redis_set(self, cache_service, redis_client):
        await cache_service.set_json("key", {"total": 0})
        redis_client.set.assert_called_once()
        call_kwargs = redis_client.set.call_args
        assert call_kwargs[0][0] == "key"
        assert "total" in call_kwargs[0][1]

    async def test_set_json_uses_default_ttl(self, cache_service, redis_client):
        await cache_service.set_json("key", {})
        _, kwargs = redis_client.set.call_args
        assert kwargs.get("ex") == 300

    async def test_set_json_custom_ttl(self, cache_service, redis_client):
        await cache_service.set_json("key", {}, ttl_seconds=60)
        _, kwargs = redis_client.set.call_args
        assert kwargs.get("ex") == 60

    async def test_set_json_silently_handles_redis_error(self, cache_service, redis_client):
        redis_client.set.side_effect = Exception("write error")
        # Не должна бросать исключение
        await cache_service.set_json("key", {"data": 1})


class TestCacheServiceDisabled:
    async def test_get_json_returns_none(self, cache_service_disabled):
        result = await cache_service_disabled.get_json("key")
        assert result is None

    async def test_set_json_does_nothing(self, cache_service_disabled):
        # Не должна бросать исключение, даже без клиента
        await cache_service_disabled.set_json("key", {"data": 1})


class TestBuildSearchKey:
    def test_same_query_produces_same_key(self):
        k1 = CacheService.build_search_key("машинное обучение", 1, 10)
        k2 = CacheService.build_search_key("машинное обучение", 1, 10)
        assert k1 == k2

    def test_normalizes_case(self):
        k1 = CacheService.build_search_key("Машинное Обучение", 1, 10)
        k2 = CacheService.build_search_key("машинное обучение", 1, 10)
        assert k1 == k2

    def test_normalizes_whitespace(self):
        k1 = CacheService.build_search_key("  тест  ", 1, 10)
        k2 = CacheService.build_search_key("тест", 1, 10)
        assert k1 == k2

    def test_different_pages_produce_different_keys(self):
        k1 = CacheService.build_search_key("query", 1, 10)
        k2 = CacheService.build_search_key("query", 2, 10)
        assert k1 != k2

    def test_different_page_sizes_produce_different_keys(self):
        k1 = CacheService.build_search_key("query", 1, 10)
        k2 = CacheService.build_search_key("query", 1, 20)
        assert k1 != k2

    def test_key_has_search_prefix(self):
        key = CacheService.build_search_key("query", 1, 10)
        assert key.startswith("search:")
