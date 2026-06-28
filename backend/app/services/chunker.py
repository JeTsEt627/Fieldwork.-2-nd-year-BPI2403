"""Разбиение извлечённого текста на чанки (BE-05).

Текст каждой страницы разбивается на сегменты фиксированного размера со
скользящим окном и перекрытием между соседними сегментами. Разбиение
выполняется в пределах одной страницы, благодаря чему за каждым чанком
сохраняется корректный номер страницы (нужно для метаданных в BE-07).
"""

from dataclasses import dataclass

from app.core.config import settings
from app.services.document_parser import ParsedPage


@dataclass(frozen=True)
class TextChunk:
    """Фрагмент текста документа.

    Attributes:
        text: Текст чанка.
        page_number: Номер страницы-источника.
        chunk_index: Порядковый номер чанка в пределах документа (с 0).
    """

    text: str
    page_number: int
    chunk_index: int


def split_text(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    """Разбить строку на чанки скользящим окном.

    Args:
        text: Исходный текст.
        chunk_size: Размер чанка в символах.
        chunk_overlap: Размер перекрытия между соседними чанками в символах.

    Returns:
        Список строк-чанков. Для пустого текста — пустой список.

    Raises:
        ValueError: Если ``chunk_size`` не положителен либо ``chunk_overlap``
            отрицателен или не меньше ``chunk_size``.
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size должен быть положительным")
    if chunk_overlap < 0:
        raise ValueError("chunk_overlap не может быть отрицательным")
    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap должен быть меньше chunk_size")

    if not text:
        return []

    step = chunk_size - chunk_overlap
    chunks: list[str] = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = start + chunk_size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= text_length:
            break
        start += step

    return chunks


def chunk_pages(
    pages: list[ParsedPage],
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> list[TextChunk]:
    """Разбить страницы документа на чанки с сохранением номеров страниц.

    Args:
        pages: Список страниц с текстом (результат работы парсера).
        chunk_size: Размер чанка; по умолчанию берётся из настроек.
        chunk_overlap: Перекрытие; по умолчанию берётся из настроек.

    Returns:
        Сквозной список чанков с метаданными (текст, страница, индекс).
    """
    size = chunk_size if chunk_size is not None else settings.chunk_size
    overlap = chunk_overlap if chunk_overlap is not None else settings.chunk_overlap

    chunks: list[TextChunk] = []
    global_index = 0

    for page in pages:
        for piece in split_text(page.text, size, overlap):
            chunks.append(
                TextChunk(
                    text=piece,
                    page_number=page.page_number,
                    chunk_index=global_index,
                )
            )
            global_index += 1

    return chunks
