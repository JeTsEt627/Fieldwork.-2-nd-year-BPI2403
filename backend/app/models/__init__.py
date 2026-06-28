"""ORM-модели приложения.

Импорт моделей здесь нужен для их регистрации в ``Base.metadata``.
"""

from app.models.document import Document, DocumentStatus
from app.models.search_history import SearchHistory

__all__ = ["Document", "DocumentStatus", "SearchHistory"]
