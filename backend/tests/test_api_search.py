"""Интеграционные тесты поискового эндпоинта (BE-08, BE-09, BE-10)."""

import pytest
from unittest.mock import AsyncMock, patch


SEARCH_RESULT = {
    "query": "машинное обучение",
    "total": 2,
    "page": 1,
    "page_size": 10,
    "took_ms": 5,
    "from_cache": False,
    "results": [
        {
            "chunk_id": "doc-1::0",
            "file_name": "lecture.pdf",
            "page": 1,
            "text": "Машинное обучение — раздел искусственного интеллекта.",
            "score": 2.5,
            "highlight": "<em>Машинное обучение</em> — раздел...",
        }
    ],
}


@pytest.mark.asyncio
class TestSearchEndpoint:
    async def test_search_returns_results(self, async_client):
        with patch(
            "app.services.search_service.perform_search",
            new=AsyncMock(return_value=SEARCH_RESULT),
        ):
            response = await async_client.get(
                "/api/v1/search", params={"q": "машинное обучение"}
            )
        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "машинное обучение"
        assert data["total"] == 2
        assert len(data["results"]) == 1

    async def test_search_result_fields_be09(self, async_client):
        """Проверить обязательные поля ответа (BE-09)."""
        with patch(
            "app.services.search_service.perform_search",
            new=AsyncMock(return_value=SEARCH_RESULT),
        ):
            response = await async_client.get(
                "/api/v1/search", params={"q": "тест"}
            )
        item = response.json()["results"][0]
        assert "chunk_id" in item
        assert "file_name" in item
        assert "page" in item
        assert "text" in item
        assert "score" in item

    async def test_search_empty_query_returns_422(self, async_client):
        response = await async_client.get("/api/v1/search", params={"q": ""})
        assert response.status_code == 422

    async def test_search_without_query_returns_422(self, async_client):
        response = await async_client.get("/api/v1/search")
        assert response.status_code == 422

    async def test_search_pagination_params(self, async_client):
        with patch(
            "app.services.search_service.perform_search",
            new=AsyncMock(return_value={**SEARCH_RESULT, "page": 2, "page_size": 5}),
        ) as mock_search:
            response = await async_client.get(
                "/api/v1/search", params={"q": "тест", "page": 2, "page_size": 5}
            )
        assert response.status_code == 200
        mock_search.assert_called_once()
        call_kwargs = mock_search.call_args.kwargs
        assert call_kwargs["page"] == 2
        assert call_kwargs["page_size"] == 5

    async def test_search_from_cache_flag(self, async_client):
        cached_result = {**SEARCH_RESULT, "from_cache": True}
        with patch(
            "app.services.search_service.perform_search",
            new=AsyncMock(return_value=cached_result),
        ):
            response = await async_client.get(
                "/api/v1/search", params={"q": "кеш"}
            )
        assert response.json()["from_cache"] is True


@pytest.mark.asyncio
class TestSearchHistoryEndpoint:
    async def test_history_returns_empty(self, async_client):
        with patch(
            "app.services.search_service.get_search_history",
            new=AsyncMock(return_value=([], 0)),
        ):
            response = await async_client.get("/api/v1/search/history")
        assert response.status_code == 200
        assert response.json()["total"] == 0
        assert response.json()["items"] == []
