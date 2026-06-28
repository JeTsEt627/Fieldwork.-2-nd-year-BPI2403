"""Оркестрация полного цикла обработки документа.

Связывает воедино парсинг (BE-04), чанкинг (BE-05) и индексацию (BE-07),
а также управляет статусом документа в PostgreSQL и записями истории поиска.
"""

import asyncio

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DocumentParsingError
from app.core.logging_config import get_logger
from app.models.document import Document, DocumentStatus
from app.services.chunker import chunk_pages
from app.services.document_parser import extract_text
from app.services.elasticsearch_service import ElasticsearchService

logger = get_logger(__name__)


async def create_document_record(
    session: AsyncSession,
    file_name: str,
    content_type: str,
    file_size: int,
) -> Document:
    """Создать запись документа в БД со статусом «загрузка» (BE-03).

    UUID генерируется автоматически на уровне ORM-модели.

    Args:
        session: Сессия БД.
        file_name: Имя файла.
        content_type: MIME-тип файла.
        file_size: Размер файла в байтах.

    Returns:
        Сохранённый объект :class:`Document`.
    """
    document = Document(
        file_name=file_name,
        content_type=content_type,
        file_size=file_size,
        status=DocumentStatus.UPLOADING,
    )
    session.add(document)
    await session.commit()
    await session.refresh(document)
    return document


async def process_and_index_document(
    session: AsyncSession,
    document: Document,
    file_bytes: bytes,
    extension: str,
    es_service: ElasticsearchService,
) -> Document:
    """Извлечь текст, разбить на чанки и проиндексировать документ.

    Обновляет статус документа по ходу обработки: ``indexing`` → ``ready``
    либо ``error`` при сбое. Парсинг выполняется в отдельном потоке, чтобы не
    блокировать событийный цикл.

    Args:
        session: Сессия БД.
        document: Запись документа, созданная ранее.
        file_bytes: Содержимое файла.
        extension: Расширение файла (``pdf``/``docx``).
        es_service: Сервис индексации в Elasticsearch.

    Returns:
        Обновлённый объект :class:`Document` со статусом ``ready``.

    Raises:
        DocumentParsingError: Если не удалось извлечь текст из документа.
    """
    try:
        document.status = DocumentStatus.INDEXING
        await session.commit()

        # Парсинг (CPU-bound) выносим из событийного цикла.
        pages = await asyncio.to_thread(extract_text, file_bytes, extension)
        chunks = chunk_pages(pages)

        indexed = await es_service.index_chunks(
            document_id=document.id,
            file_name=document.file_name,
            chunks=chunks,
        )

        document.status = DocumentStatus.READY
        document.chunk_count = indexed
        document.page_count = max((page.page_number for page in pages), default=0)
        document.error_message = None
        await session.commit()
        await session.refresh(document)

        logger.info(
            "Документ %s обработан: %d страниц, %d чанков",
            document.id,
            document.page_count,
            document.chunk_count,
        )
        return document

    except Exception as exc:
        # Фиксируем статус ошибки, чтобы он отобразился на фронтенде (FE-02).
        document.status = DocumentStatus.ERROR
        document.error_message = str(exc)
        await session.commit()
        logger.exception("Ошибка обработки документа %s", document.id)
        if isinstance(exc, DocumentParsingError):
            raise
        raise DocumentParsingError(str(exc)) from exc


async def list_documents(
    session: AsyncSession, limit: int = 50, offset: int = 0
) -> tuple[list[Document], int]:
    """Вернуть список документов с пагинацией (FE-03).

    Args:
        session: Сессия БД.
        limit: Максимальное количество записей.
        offset: Смещение от начала выборки.

    Returns:
        Кортеж ``(документы, общее_количество)``.
    """
    total = await session.scalar(select(func.count()).select_from(Document))
    result = await session.execute(
        select(Document)
        .order_by(Document.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    documents = list(result.scalars().all())
    return documents, int(total or 0)


async def get_document(session: AsyncSession, document_id: str) -> Document | None:
    """Получить документ по идентификатору.

    Args:
        session: Сессия БД.
        document_id: UUID документа.

    Returns:
        Объект :class:`Document` либо ``None``, если не найден.
    """
    return await session.get(Document, document_id)


async def delete_document(
    session: AsyncSession,
    document: Document,
    es_service: ElasticsearchService,
) -> None:
    """Удалить документ из БД и его чанки из индекса.

    Args:
        session: Сессия БД.
        document: Удаляемый документ.
        es_service: Сервис Elasticsearch для удаления чанков.
    """
    await es_service.delete_document(document.id)
    await session.delete(document)
    await session.commit()
