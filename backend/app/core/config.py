"""Конфигурация приложения.

Все настройки читаются из переменных окружения (или файла ``.env``) через
``pydantic-settings``. Это позволяет не хранить конфиденциальные данные
(пароли, ключи) в коде согласно требованию DO-04.
"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Набор настроек приложения, загружаемых из окружения.

    Attributes:
        app_name: Человекочитаемое название сервиса.
        api_v1_prefix: Префикс для всех эндпоинтов первой версии API.
        max_upload_size_mb: Максимально допустимый размер загружаемого файла, МБ.
        chunk_size: Размер чанка текста в символах (BE-05).
        chunk_overlap: Перекрытие между соседними чанками в символах (BE-05).
        postgres_*: Параметры подключения к PostgreSQL.
        elasticsearch_url: URL кластера Elasticsearch.
        elasticsearch_index: Имя индекса для хранения чанков документов.
        redis_url: URL подключения к Redis.
        cache_ttl_seconds: Время жизни записи в кеше поиска (BE-10).
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- Общие параметры приложения ---
    app_name: str = "University Knowledge Search API"
    app_version: str = "1.0.0"
    api_v1_prefix: str = "/api/v1"
    debug: bool = False

    # --- Ограничения загрузки и обработки документов ---
    max_upload_size_mb: int = 20
    allowed_extensions: set[str] = {"pdf", "docx"}
    chunk_size: int = 1000
    chunk_overlap: int = 100

    # --- PostgreSQL ---
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "knowledge"
    postgres_password: str = "knowledge"
    postgres_db: str = "knowledge_base"

    # --- Elasticsearch ---
    elasticsearch_url: str = "http://localhost:9200"
    elasticsearch_index: str = "documents"

    # --- Redis ---
    redis_url: str = "redis://localhost:6379/0"
    cache_ttl_seconds: int = 300  # 5 минут (BE-10)
    cache_enabled: bool = True

    # --- Прочее ---
    search_default_size: int = Field(default=10, ge=1, le=100)

    @property
    def max_upload_size_bytes(self) -> int:
        """Максимальный размер файла в байтах."""
        return self.max_upload_size_mb * 1024 * 1024

    @property
    def database_url(self) -> str:
        """Строка подключения SQLAlchemy для асинхронного драйвера asyncpg."""
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache
def get_settings() -> Settings:
    """Вернуть кешированный экземпляр настроек.

    Использование ``lru_cache`` гарантирует, что окружение читается один раз
    за время жизни процесса.

    Returns:
        Единственный экземпляр :class:`Settings`.
    """
    return Settings()


settings = get_settings()
