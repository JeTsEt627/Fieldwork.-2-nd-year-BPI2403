"""ORM-модель загруженного документа."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class DocumentStatus(str, enum.Enum):
    """Статус обработки документа.

    Значения соответствуют состояниям, отображаемым на фронтенде (FE-02):
    загрузка, индексация, готово, ошибка.
    """

    UPLOADING = "uploading"
    INDEXING = "indexing"
    READY = "ready"
    ERROR = "error"


class Document(Base):
    """Метаданные загруженного документа.

    Сам файл не хранится в БД; в PostgreSQL сохраняется информация о документе,
    а текстовые чанки индексируются в Elasticsearch.

    Attributes:
        id: Уникальный идентификатор документа (UUID, BE-03).
        file_name: Исходное имя файла.
        content_type: MIME-тип файла.
        file_size: Размер файла в байтах.
        status: Текущий статус обработки.
        chunk_count: Количество проиндексированных чанков.
        page_count: Количество страниц в документе.
        error_message: Текст ошибки, если обработка завершилась неудачей.
        created_at: Дата и время загрузки.
        updated_at: Дата и время последнего изменения записи.
    """

    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    file_name: Mapped[str] = mapped_column(String(512), nullable=False)
    content_type: Mapped[str] = mapped_column(String(128), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[DocumentStatus] = mapped_column(
        Enum(DocumentStatus, native_enum=False, length=20),
        default=DocumentStatus.UPLOADING,
        nullable=False,
    )
    chunk_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    page_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:  # pragma: no cover - вспомогательный метод
        return f"<Document id={self.id} file_name={self.file_name!r} status={self.status}>"
