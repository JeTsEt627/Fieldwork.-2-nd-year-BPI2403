"""Схемы данных, связанные с документами."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.document import DocumentStatus


class DocumentResponse(BaseModel):
    """Информация о документе, возвращаемая клиенту."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Уникальный идентификатор документа (UUID)")
    file_name: str = Field(..., description="Исходное имя файла")
    content_type: str = Field(..., description="MIME-тип файла")
    file_size: int = Field(..., description="Размер файла в байтах")
    status: DocumentStatus = Field(..., description="Статус обработки документа")
    chunk_count: int = Field(..., description="Количество проиндексированных чанков")
    page_count: int = Field(..., description="Количество страниц в документе")
    error_message: str | None = Field(
        None, description="Описание ошибки, если обработка не удалась"
    )
    created_at: datetime = Field(..., description="Дата и время загрузки")
    updated_at: datetime = Field(..., description="Дата и время последнего изменения")


class DocumentUploadResponse(BaseModel):
    """Ответ на успешную загрузку документа (BE-01)."""

    id: str = Field(..., description="Уникальный идентификатор документа (UUID)")
    file_name: str = Field(..., description="Исходное имя файла")
    status: DocumentStatus = Field(..., description="Статус обработки документа")
    chunk_count: int = Field(..., description="Количество проиндексированных чанков")
    page_count: int = Field(..., description="Количество страниц в документе")
    message: str = Field(..., description="Человекочитаемое сообщение о результате")


class DocumentListResponse(BaseModel):
    """Список документов с информацией о пагинации (FE-03)."""

    total: int = Field(..., description="Общее количество документов")
    items: list[DocumentResponse] = Field(..., description="Документы текущей страницы")
