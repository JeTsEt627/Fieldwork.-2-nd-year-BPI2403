"""Проверка обработки «проблемного» набора документов QA-03.

Тесты пропускаются, если фикстуры ещё не сгенерированы
(см. ``tests/fixtures/generate_fixtures.py``).
"""

import os

import pytest

from app.core.exceptions import DocumentParsingError, EmptyDocumentError
from app.services.document_parser import extract_text

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


def _fixture(name: str) -> str:
    return os.path.join(FIXTURES_DIR, name)


def _read(name: str) -> bytes:
    with open(_fixture(name), "rb") as fh:
        return fh.read()


def _exists(name: str) -> bool:
    return os.path.isfile(_fixture(name))


class TestValidDocuments:
    @pytest.mark.skipif(
        not _exists("valid_document.docx"), reason="фикстура не сгенерирована"
    )
    def test_valid_docx_extracts_text(self):
        pages = extract_text(_read("valid_document.docx"), "docx")
        assert len(pages) >= 1
        assert "обучение" in pages[0].text.lower()

    @pytest.mark.skipif(
        not _exists("valid_document.pdf"), reason="фикстура не сгенерирована"
    )
    def test_valid_pdf_extracts_text(self):
        pages = extract_text(_read("valid_document.pdf"), "pdf")
        assert len(pages) >= 1


class TestEmptyDocuments:
    @pytest.mark.skipif(
        not _exists("empty_document.docx"), reason="фикстура не сгенерирована"
    )
    def test_empty_docx_raises(self):
        with pytest.raises(EmptyDocumentError):
            extract_text(_read("empty_document.docx"), "docx")


class TestCorruptedDocuments:
    @pytest.mark.skipif(
        not _exists("corrupted.pdf"), reason="фикстура не сгенерирована"
    )
    def test_corrupted_pdf_raises(self):
        with pytest.raises(DocumentParsingError):
            extract_text(_read("corrupted.pdf"), "pdf")

    @pytest.mark.skipif(
        not _exists("corrupted.docx"), reason="фикстура не сгенерирована"
    )
    def test_corrupted_docx_raises(self):
        with pytest.raises(DocumentParsingError):
            extract_text(_read("corrupted.docx"), "docx")
