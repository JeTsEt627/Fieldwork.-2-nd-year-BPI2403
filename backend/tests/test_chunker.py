"""Юнит-тесты разбиения текста на чанки (BE-05)."""

import pytest

from app.services.chunker import TextChunk, chunk_pages, split_text
from app.services.document_parser import ParsedPage


class TestSplitText:
    def test_short_text_returns_single_chunk(self):
        result = split_text("Hello world", chunk_size=1000, chunk_overlap=100)
        assert result == ["Hello world"]

    def test_exact_chunk_size(self):
        text = "a" * 1000
        result = split_text(text, chunk_size=1000, chunk_overlap=0)
        assert len(result) == 1
        assert result[0] == text

    def test_splits_into_multiple_chunks(self):
        text = "a" * 2000
        result = split_text(text, chunk_size=1000, chunk_overlap=0)
        assert len(result) == 2

    def test_overlap_causes_extra_chunk(self):
        # При size=100, overlap=10 и тексте 150 символов должно быть 2 чанка:
        # [0:100] и [90:150]
        text = "x" * 150
        result = split_text(text, chunk_size=100, chunk_overlap=10)
        assert len(result) == 2

    def test_empty_text_returns_empty_list(self):
        assert split_text("", chunk_size=100, chunk_overlap=0) == []

    def test_whitespace_only_returns_empty_list(self):
        assert split_text("   \n\t  ", chunk_size=100, chunk_overlap=0) == []

    def test_invalid_chunk_size_raises(self):
        with pytest.raises(ValueError, match="chunk_size"):
            split_text("text", chunk_size=0, chunk_overlap=0)

    def test_negative_chunk_size_raises(self):
        with pytest.raises(ValueError, match="chunk_size"):
            split_text("text", chunk_size=-10, chunk_overlap=0)

    def test_negative_overlap_raises(self):
        with pytest.raises(ValueError, match="chunk_overlap"):
            split_text("text", chunk_size=100, chunk_overlap=-1)

    def test_overlap_gte_size_raises(self):
        with pytest.raises(ValueError, match="chunk_overlap"):
            split_text("text", chunk_size=100, chunk_overlap=100)

    def test_chunks_cover_all_text(self):
        text = "abcdefghij" * 20  # 200 символов
        result = split_text(text, chunk_size=100, chunk_overlap=10)
        # Первый чанк начинается с начала текста
        assert text.startswith(result[0][:10])
        # Последний чанк содержит конец текста
        assert text.endswith(result[-1][-10:])


class TestChunkPages:
    def test_single_page_produces_chunks(self):
        pages = [ParsedPage(page_number=1, text="word " * 300)]
        chunks = chunk_pages(pages, chunk_size=100, chunk_overlap=10)
        assert len(chunks) > 0
        assert all(isinstance(c, TextChunk) for c in chunks)

    def test_chunk_page_numbers_preserved(self):
        pages = [
            ParsedPage(page_number=1, text="A" * 200),
            ParsedPage(page_number=2, text="B" * 200),
        ]
        chunks = chunk_pages(pages, chunk_size=100, chunk_overlap=0)
        page1_chunks = [c for c in chunks if c.page_number == 1]
        page2_chunks = [c for c in chunks if c.page_number == 2]
        assert len(page1_chunks) > 0
        assert len(page2_chunks) > 0

    def test_chunk_indices_are_sequential(self):
        pages = [ParsedPage(page_number=1, text="X" * 500)]
        chunks = chunk_pages(pages, chunk_size=100, chunk_overlap=0)
        indices = [c.chunk_index for c in chunks]
        assert indices == list(range(len(chunks)))

    def test_empty_pages_returns_empty(self):
        assert chunk_pages([]) == []

    def test_global_index_spans_pages(self):
        pages = [
            ParsedPage(page_number=1, text="A" * 200),
            ParsedPage(page_number=2, text="B" * 200),
        ]
        chunks = chunk_pages(pages, chunk_size=100, chunk_overlap=0)
        indices = [c.chunk_index for c in chunks]
        # Индексы должны быть сплошными и начинаться с 0
        assert indices == list(range(len(chunks)))
