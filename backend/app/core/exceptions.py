"""Доменные исключения приложения.

Исключения отделяют бизнес-логику от HTTP-слоя: сервисы выбрасывают эти
ошибки, а обработчики в ``main.py`` преобразуют их в корректные HTTP-ответы.
"""


class AppError(Exception):
    """Базовое исключение приложения."""


class ValidationError(AppError):
    """Ошибка валидации входных данных (приводит к HTTP 400)."""


class UnsupportedFormatError(ValidationError):
    """Загружен файл неподдерживаемого формата (не PDF/DOCX)."""


class FileTooLargeError(ValidationError):
    """Размер файла превышает допустимый лимит."""


class EmptyFileError(ValidationError):
    """Загружен пустой файл."""


class DocumentParsingError(AppError):
    """Не удалось извлечь текст из документа."""


class EmptyDocumentError(DocumentParsingError):
    """Документ не содержит извлекаемого текста."""


class SearchServiceError(AppError):
    """Ошибка при выполнении поиска в Elasticsearch."""


class ResourceNotFoundError(AppError):
    """Запрошенный ресурс не найден (приводит к HTTP 404)."""
