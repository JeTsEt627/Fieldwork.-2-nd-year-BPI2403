"""Эндпоинты модуля загрузки и обработки документов (BE-01 – BE-05)."""

from fastapi import APIRouter, File, Query, UploadFile, status

from app.api.dependencies import DbSession, EsService
from app.core.exceptions import ResourceNotFoundError
from app.core.logging_config import get_logger
from app.schemas.document import (
    DocumentListResponse,
    DocumentResponse,
    DocumentUploadResponse,
)
from app.services import document_service
from app.services.file_validation import validate_upload

logger = get_logger(__name__)

router = APIRouter(prefix="/documents", tags=["Документы"])


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Загрузить и проиндексировать документ",
    responses={
        201: {"description": "Документ успешно загружен и проиндексирован"},
        400: {"description": "Ошибка валидации файла (формат, размер, содержимое)"},
    },
)
async def upload_document(
    session: DbSession,
    es_service: EsService,
    file: UploadFile = File(..., description="Файл PDF или DOCX (не более 20 МБ)"),
) -> DocumentUploadResponse:
    """Загрузить документ, извлечь текст и проиндексировать его.

    Реализует требования BE-01 (эндпоинт загрузки), BE-02 (валидация формата
    и размера), BE-03 (генерация UUID), BE-04 (извлечение текста), BE-05
    (чанкинг) и BE-07 (индексация чанков).

    Args:
        session: Сессия БД (внедряется).
        es_service: Сервис Elasticsearch (внедряется).
        file: Загружаемый файл.

    Returns:
        Информация о созданном документе и результате индексации.

    Raises:
        ValidationError: Файл не прошёл валидацию (приводит к HTTP 400).
        DocumentParsingError: Не удалось извлечь текст (приводит к HTTP 400).
    """
    # Читаем содержимое файла, чтобы определить реальный размер (BE-02).
    file_bytes = await file.read()
    file_size = len(file_bytes)

    # Валидация формата и размера (BE-02). Выбрасывает ValidationError → 400.
    extension = validate_upload(
        file_name=file.filename or "",
        file_size=file_size,
        content_type=file.content_type,
    )

    # Создаём запись с уникальным UUID (BE-03).
    document = await document_service.create_document_record(
        session=session,
        file_name=file.filename or f"document.{extension}",
        content_type=file.content_type or "application/octet-stream",
        file_size=file_size,
    )

    # Парсинг, чанкинг и индексация (BE-04, BE-05, BE-07).
    document = await document_service.process_and_index_document(
        session=session,
        document=document,
        file_bytes=file_bytes,
        extension=extension,
        es_service=es_service,
    )

    return DocumentUploadResponse(
        id=document.id,
        file_name=document.file_name,
        status=document.status,
        chunk_count=document.chunk_count,
        page_count=document.page_count,
        message="Документ успешно загружен и проиндексирован",
    )


@router.get(
    "",
    response_model=DocumentListResponse,
    summary="Список загруженных документов",
)
async def list_documents(
    session: DbSession,
    limit: int = Query(50, ge=1, le=200, description="Размер страницы"),
    offset: int = Query(0, ge=0, description="Смещение"),
) -> DocumentListResponse:
    """Вернуть список загруженных документов (FE-03).

    Args:
        session: Сессия БД (внедряется).
        limit: Максимальное количество записей на странице.
        offset: Смещение от начала выборки.

    Returns:
        Список документов и общее количество.
    """
    documents, total = await document_service.list_documents(session, limit, offset)
    return DocumentListResponse(
        total=total,
        items=[DocumentResponse.model_validate(doc) for doc in documents],
    )


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
    summary="Получить документ по идентификатору",
    responses={404: {"description": "Документ не найден"}},
)
async def get_document(session: DbSession, document_id: str) -> DocumentResponse:
    """Вернуть метаданные документа по его UUID.

    Args:
        session: Сессия БД (внедряется).
        document_id: UUID документа.

    Returns:
        Метаданные документа.

    Raises:
        ResourceNotFoundError: Документ не найден (приводит к HTTP 404).
    """
    document = await document_service.get_document(session, document_id)
    if document is None:
        raise ResourceNotFoundError(f"Документ с id={document_id} не найден")
    return DocumentResponse.model_validate(document)


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить документ",
    responses={404: {"description": "Документ не найден"}},
)
async def delete_document(
    session: DbSession, es_service: EsService, document_id: str
) -> None:
    """Удалить документ и связанные с ним чанки из индекса.

    Args:
        session: Сессия БД (внедряется).
        es_service: Сервис Elasticsearch (внедряется).
        document_id: UUID документа.

    Raises:
        ResourceNotFoundError: Документ не найден (приводит к HTTP 404).
    """
    document = await document_service.get_document(session, document_id)
    if document is None:
        raise ResourceNotFoundError(f"Документ с id={document_id} не найден")
    await document_service.delete_document(session, document, es_service)
