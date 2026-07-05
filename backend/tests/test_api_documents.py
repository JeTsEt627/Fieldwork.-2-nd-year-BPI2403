"""Интеграционные тесты эндпоинтов документов (BE-01, BE-02)."""

import io
from datetime import UTC
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.document import Document, DocumentStatus


def make_document(**kwargs) -> Document:
    defaults = dict(
        id="test-uuid-1234",
        file_name="test.pdf",
        content_type="application/pdf",
        file_size=1024,
        status=DocumentStatus.READY,
        chunk_count=5,
        page_count=2,
        error_message=None,
    )
    defaults.update(kwargs)
    doc = MagicMock(spec=Document)
    for k, v in defaults.items():
        setattr(doc, k, v)
    return doc


@pytest.mark.asyncio
class TestUploadDocument:
    async def test_upload_valid_pdf(self, async_client, mock_es_service, mock_db_session):
        doc = make_document()
        mock_db_session.refresh = AsyncMock(side_effect=lambda obj: None)

        with (
            patch("app.services.document_service.create_document_record", new=AsyncMock(return_value=doc)),
            patch("app.services.document_service.process_and_index_document", new=AsyncMock(return_value=doc)),
        ):
            response = await async_client.post(
                "/api/v1/documents/upload",
                files={"file": ("test.pdf", io.BytesIO(b"%PDF-1.4 test"), "application/pdf")},
            )

        assert response.status_code == 201
        data = response.json()
        assert data["id"] == "test-uuid-1234"
        assert data["file_name"] == "test.pdf"
        assert data["status"] == "ready"

    async def test_upload_rejects_txt_file(self, async_client):
        response = await async_client.post(
            "/api/v1/documents/upload",
            files={"file": ("notes.txt", io.BytesIO(b"plain text"), "text/plain")},
        )
        assert response.status_code == 400

    async def test_upload_rejects_empty_file(self, async_client):
        response = await async_client.post(
            "/api/v1/documents/upload",
            files={"file": ("empty.pdf", io.BytesIO(b""), "application/pdf")},
        )
        assert response.status_code == 400

    async def test_upload_without_file_returns_422(self, async_client):
        response = await async_client.post("/api/v1/documents/upload")
        assert response.status_code == 422


@pytest.mark.asyncio
class TestListDocuments:
    async def test_returns_empty_list(self, async_client, mock_db_session):
        with patch(
            "app.services.document_service.list_documents",
            new=AsyncMock(return_value=([], 0)),
        ):
            response = await async_client.get("/api/v1/documents")
        assert response.status_code == 200
        assert response.json()["total"] == 0
        assert response.json()["items"] == []

    async def test_returns_documents(self, async_client, mock_db_session):
        from datetime import datetime
        doc = make_document()
        doc.created_at = datetime(2024, 1, 1, tzinfo=UTC)
        doc.updated_at = datetime(2024, 1, 1, tzinfo=UTC)

        with patch(
            "app.services.document_service.list_documents",
            new=AsyncMock(return_value=([doc], 1)),
        ):
            response = await async_client.get("/api/v1/documents")
        assert response.status_code == 200
        assert response.json()["total"] == 1


@pytest.mark.asyncio
class TestGetDocument:
    async def test_not_found_returns_404(self, async_client, mock_db_session):
        with patch(
            "app.services.document_service.get_document",
            new=AsyncMock(return_value=None),
        ):
            response = await async_client.get("/api/v1/documents/nonexistent-id")
        assert response.status_code == 404

    async def test_found_returns_200(self, async_client, mock_db_session):
        from datetime import datetime
        doc = make_document()
        doc.created_at = datetime(2024, 1, 1, tzinfo=UTC)
        doc.updated_at = datetime(2024, 1, 1, tzinfo=UTC)

        with patch(
            "app.services.document_service.get_document",
            new=AsyncMock(return_value=doc),
        ):
            response = await async_client.get("/api/v1/documents/test-uuid-1234")
        assert response.status_code == 200
        assert response.json()["id"] == "test-uuid-1234"
