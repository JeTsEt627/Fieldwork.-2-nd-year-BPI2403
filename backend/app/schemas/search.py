"""Схемы данных для поиска (BE-08, BE-09)."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SearchResultItem(BaseModel):
    """Один результат поиска — фрагмент (чанк) документа.

    Набор полей соответствует требованию BE-09.
    """

    chunk_id: str = Field(..., description="Идентификатор чанка")
    file_name: str = Field(..., description="Имя файла-источника")
    page: int = Field(..., description="Номер страницы, где найден фрагмент")
    text: str = Field(..., description="Текст найденного фрагмента")
    score: float = Field(..., description="Оценка релевантности (Elasticsearch _score)")
    highlight: str | None = Field(
        None,
        description="Фрагмент с HTML-подсветкой совпадений (<em>...</em>)",
    )


class SearchResponse(BaseModel):
    """Полный ответ поискового эндпоинта."""

    query: str = Field(..., description="Исходный поисковый запрос")
    total: int = Field(..., description="Общее количество найденных фрагментов")
    page: int = Field(..., description="Номер текущей страницы (с 1)")
    page_size: int = Field(..., description="Количество результатов на странице")
    took_ms: int = Field(..., description="Время выполнения запроса в миллисекундах")
    from_cache: bool = Field(..., description="Был ли ответ взят из кеша Redis")
    results: list[SearchResultItem] = Field(..., description="Найденные фрагменты")


class SearchHistoryItem(BaseModel):
    """Одна запись истории поиска."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="Идентификатор записи")
    query: str = Field(..., description="Текст запроса")
    results_count: int = Field(..., description="Количество найденных результатов")
    from_cache: bool = Field(..., description="Ответ был взят из кеша")
    created_at: datetime = Field(..., description="Дата и время запроса")


class SearchHistoryResponse(BaseModel):
    """Список записей истории поиска."""

    total: int = Field(..., description="Общее количество записей истории")
    items: list[SearchHistoryItem] = Field(..., description="Записи истории")
