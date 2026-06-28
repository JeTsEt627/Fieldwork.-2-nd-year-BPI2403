"""Юнит-тесты сервиса Elasticsearch (BE-06, BE-07, BE-08)."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.core.exceptions import SearchServiceError
from app.services.chunker import TextChunk
from app.services.elasticsearch_service import (
    ElasticsearchService,
    build_chunk_id,
)


# --------------------------------------------------------------------------- #
# build_chunk_id                                                               #
# --------------------------------------------------------------------------- #

class TestBuildChunkId:
    def test_format(self):
        result = build_chunk_id("abc-123", 0)
        assert result == "abc-123::0"

    def test_different_indices(self):
        assert build_chunk_id("doc", 1) != build_chunk_id("doc", 2)

    def test_different_documents(self):
        assert build_chunk_id("doc1", 0) != build_chunk_id("doc2", 0)


# --------------------------------------------------------------------------- #
# ElasticsearchService                                                         #
# --------------------------------------------------------------------------- #

@pytest.fixture
def mock_es_client():
    client = MagicMock()
    client.ping = AsyncMock(return_value=True)
    client.indices = MagicMock()
    client.indices.exists = AsyncMock(return_value=False)
    client.indices.create = AsyncMock()
    client.search = AsyncMock()
    client.delete_by_query = AsyncMock(return_value={"deleted": 3})
    return client


@pytest.fixture
def es_service(mock_es_client) -> ElasticsearchService:
    return ElasticsearchService(mock_es_client, "test_index")


class TestPing:
    async def test_returns_true_when_reachable(self, es_service, mock_es_client):
        mock_es_client.ping.return_value = True
        assert await es_service.ping() is True

    async def test_returns_false_on_exception(self, es_service, mock_es_client):
        mock_es_client.ping.side_effect = Exception("timeout")
        assert await es_service.ping() is False


class TestEnsureIndex:
    async def test_creates_index_when_not_exists(self, es_service, mock_es_client):
        mock_es_client.indices.exists.return_value = False
        await es_service.ensure_index()
        mock_es_client.indices.create.assert_called_once()

    async def test_skips_creation_when_exists(self, es_service, mock_es_client):
        mock_es_client.indices.exists.return_value = True
        await es_service.ensure_index()
        mock_es_client.indices.create.assert_not_called()

    async def test_raises_search_service_error_on_failure(self, es_service, mock_es_client):
        mock_es_client.indices.exists.side_effect = Exception("connection refused")
        with pytest.raises(SearchServiceError):
            await es_service.ensure_index()


class TestIndexChunks:
    async def test_returns_zero_for_empty_chunks(self, es_service):
        result = await es_service.index_chunks("doc-1", "file.pdf", [])
        assert result == 0

    async def test_indexes_all_chunks(self, es_service):
        chunks = [
            TextChunk(text=f"Chunk {i}", page_number=1, chunk_index=i)
            for i in range(3)
        ]
        with patch(
            "app.services.elasticsearch_service.async_bulk",
            new=AsyncMock(return_value=(3, [])),
        ):
            result = await es_service.index_chunks("doc-1", "file.pdf", chunks)
        assert result == 3

    async def test_raises_on_bulk_errors(self, es_service):
        chunks = [TextChunk(text="text", page_number=1, chunk_index=0)]
        with patch(
            "app.services.elasticsearch_service.async_bulk",
            new=AsyncMock(return_value=(0, ["error"])),
        ):
            with pytest.raises(SearchServiceError):
                await es_service.index_chunks("doc-1", "file.pdf", chunks)


class TestSearch:
    async def test_returns_formatted_response(self, es_service, mock_es_client):
        mock_es_client.search.return_value = {
            "took": 5,
            "hits": {
                "total": {"value": 1},
                "hits": [
                    {
                        "_id": "doc-1::0",
                        "_score": 1.5,
                        "_source": {
                            "chunk_id": "doc-1::0",
                            "file_name": "test.pdf",
                            "page_number": 1,
                            "text": "relevant text",
                        },
                    }
                ],
            },
        }
        result = await es_service.search("relevant")
        assert result["total"] == 1
        assert result["took_ms"] == 5
        assert len(result["results"]) == 1
        assert result["results"][0]["file_name"] == "test.pdf"
        assert result["results"][0]["score"] == 1.5

    async def test_raises_search_service_error_on_exception(self, es_service, mock_es_client):
        mock_es_client.search.side_effect = Exception("cluster error")
        with pytest.raises(SearchServiceError):
            await es_service.search("query")

    async def test_empty_results(self, es_service, mock_es_client):
        mock_es_client.search.return_value = {
            "took": 1,
            "hits": {"total": {"value": 0}, "hits": []},
        }
        result = await es_service.search("nothing")
        assert result["total"] == 0
        assert result["results"] == []


class TestDeleteDocument:
    async def test_returns_deleted_count(self, es_service, mock_es_client):
        mock_es_client.delete_by_query.return_value = {"deleted": 5}
        count = await es_service.delete_document("doc-1")
        assert count == 5

    async def test_raises_on_exception(self, es_service, mock_es_client):
        mock_es_client.delete_by_query.side_effect = Exception("error")
        with pytest.raises(SearchServiceError):
            await es_service.delete_document("doc-1")
