"""ORM-модель истории поисковых запросов."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class SearchHistory(Base):
    """Запись об одном поисковом запросе пользователя.

    Сохранение истории требуется общими функциональными требованиями
    («Сохранение истории поисковых запросов»).

    Attributes:
        id: Автоинкрементный идентификатор записи.
        query: Текст поискового запроса.
        results_count: Количество найденных результатов.
        from_cache: Был ли ответ взят из кеша Redis (BE-10).
        created_at: Дата и время выполнения запроса.
    """

    __tablename__ = "search_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    query: Mapped[str] = mapped_column(String(1024), nullable=False, index=True)
    results_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    from_cache: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:  # pragma: no cover - вспомогательный метод
        return f"<SearchHistory id={self.id} query={self.query!r}>"
