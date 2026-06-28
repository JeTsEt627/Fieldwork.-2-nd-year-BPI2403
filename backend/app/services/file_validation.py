"""Валидация загружаемых файлов (BE-02).

Проверяются формат (расширение и MIME-тип) и размер файла. При нарушении
правил выбрасываются доменные исключения, которые HTTP-слой преобразует в
ответ ``400 Bad Request`` с понятным описанием ошибки.
"""

import os

from app.core.config import settings
from app.core.exceptions import (
    EmptyFileError,
    FileTooLargeError,
    UnsupportedFormatError,
)

# Допустимые MIME-типы для каждого расширения.
ALLOWED_CONTENT_TYPES: dict[str, set[str]] = {
    "pdf": {"application/pdf"},
    "docx": {
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        # Некоторые клиенты присылают обобщённые типы — допускаем их.
        "application/octet-stream",
        "application/zip",
    },
}


def get_file_extension(file_name: str) -> str:
    """Вернуть расширение файла в нижнем регистре без точки.

    Args:
        file_name: Имя файла.

    Returns:
        Расширение (например, ``"pdf"``) либо пустая строка, если его нет.
    """
    _, ext = os.path.splitext(file_name or "")
    return ext.lower().lstrip(".")


def validate_extension(file_name: str) -> str:
    """Проверить, что расширение файла разрешено.

    Args:
        file_name: Имя загружаемого файла.

    Returns:
        Нормализованное расширение файла.

    Raises:
        UnsupportedFormatError: Расширение отсутствует или не входит в список
            разрешённых (PDF, DOCX).
    """
    extension = get_file_extension(file_name)
    if not extension:
        raise UnsupportedFormatError(
            "У файла отсутствует расширение. Допустимы только PDF и DOCX."
        )
    if extension not in settings.allowed_extensions:
        allowed = ", ".join(sorted(settings.allowed_extensions)).upper()
        raise UnsupportedFormatError(
            f"Формат '{extension}' не поддерживается. Допустимы только: {allowed}."
        )
    return extension


def validate_size(file_size: int) -> None:
    """Проверить размер файла.

    Args:
        file_size: Размер файла в байтах.

    Raises:
        EmptyFileError: Файл пустой (0 байт).
        FileTooLargeError: Размер превышает лимит из настроек (по умолчанию 20 МБ).
    """
    if file_size <= 0:
        raise EmptyFileError("Загружен пустой файл.")
    if file_size > settings.max_upload_size_bytes:
        raise FileTooLargeError(
            f"Размер файла ({file_size / 1024 / 1024:.2f} МБ) превышает "
            f"допустимый лимит {settings.max_upload_size_mb} МБ."
        )


def validate_upload(file_name: str, file_size: int, content_type: str | None) -> str:
    """Выполнить полную валидацию загружаемого файла (BE-02).

    Args:
        file_name: Имя файла.
        file_size: Размер файла в байтах.
        content_type: MIME-тип, переданный клиентом (может быть ``None``).

    Returns:
        Нормализованное расширение файла.

    Raises:
        UnsupportedFormatError: Недопустимый формат или несоответствие MIME-типа.
        EmptyFileError: Пустой файл.
        FileTooLargeError: Превышен лимит размера.
    """
    extension = validate_extension(file_name)
    validate_size(file_size)

    # MIME-тип проверяем мягко: ориентируемся в первую очередь на расширение,
    # но отклоняем явно противоречащий тип (например, image/png для .pdf).
    if content_type:
        allowed_types = ALLOWED_CONTENT_TYPES.get(extension, set())
        normalized = content_type.split(";")[0].strip().lower()
        if normalized and normalized not in allowed_types:
            raise UnsupportedFormatError(
                f"MIME-тип '{normalized}' не соответствует формату '{extension}'."
            )

    return extension
