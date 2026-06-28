"""Точка входа приложения FastAPI.

Собирает приложение: подключает роутеры, настраивает CORS, регистрирует
обработчики доменных исключений (корректные HTTP-статусы 400/404/500) и
управляет жизненным циклом внешних клиентов (Elasticsearch, Redis, БД).
Документация OpenAPI 3.0 доступна по ``/docs`` (Swagger UI) и ``/redoc``.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import documents, search
from app.core.clients import (
    get_cache_service,
    get_es_service,
    shutdown_clients,
    startup_clients,
)
from app.core.config import settings
from app.core.database import init_models
from app.core.exceptions import (
    AppError,
    DocumentParsingError,
    ResourceNotFoundError,
    SearchServiceError,
    ValidationError,
)
from app.core.logging_config import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения.

    На старте создаёт таблицы БД и подключает внешних клиентов; при остановке
    корректно закрывает соединения.
    """
    logger.info("Запуск приложения %s", settings.app_name)
    try:
        await init_models()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Не удалось инициализировать таблицы БД при старте: %s", exc)
    await startup_clients()
    yield
    await shutdown_clients()
    logger.info("Приложение остановлено")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "Интеллектуальная поисковая система по внутренней базе знаний "
        "университета. Поддерживает загрузку PDF/DOCX, извлечение текста, "
        "индексацию в Elasticsearch и полнотекстовый поиск с подсветкой."
    ),
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS для взаимодействия с фронтендом (клиент-серверное взаимодействие).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Обработчики доменных исключений → корректные HTTP-статусы ---


@app.exception_handler(ValidationError)
async def handle_validation_error(_: Request, exc: ValidationError) -> JSONResponse:
    """Преобразовать ошибку валидации в ответ 400 Bad Request."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST, content={"detail": str(exc)}
    )


@app.exception_handler(DocumentParsingError)
async def handle_parsing_error(_: Request, exc: DocumentParsingError) -> JSONResponse:
    """Преобразовать ошибку парсинга документа в ответ 400 Bad Request."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST, content={"detail": str(exc)}
    )


@app.exception_handler(ResourceNotFoundError)
async def handle_not_found(_: Request, exc: ResourceNotFoundError) -> JSONResponse:
    """Преобразовать отсутствие ресурса в ответ 404 Not Found."""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND, content={"detail": str(exc)}
    )


@app.exception_handler(SearchServiceError)
async def handle_search_error(_: Request, exc: SearchServiceError) -> JSONResponse:
    """Преобразовать недоступность поиска в ответ 503 Service Unavailable."""
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"detail": str(exc)},
    )


@app.exception_handler(AppError)
async def handle_app_error(_: Request, exc: AppError) -> JSONResponse:
    """Преобразовать прочие доменные ошибки в ответ 500 Internal Server Error."""
    logger.exception("Необработанная доменная ошибка: %s", exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Внутренняя ошибка сервера"},
    )


# --- Роутеры ---
app.include_router(documents.router, prefix=settings.api_v1_prefix)
app.include_router(search.router, prefix=settings.api_v1_prefix)


# --- Служебные эндпоинты ---


@app.get("/health", tags=["Служебные"], summary="Проверка состояния сервиса")
async def health() -> dict:
    """Вернуть состояние сервиса и его зависимостей.

    Returns:
        Словарь со статусом приложения, Elasticsearch и Redis.
    """
    es_ok = await get_es_service().ping()
    redis_ok = await get_cache_service().ping()
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": settings.app_version,
        "elasticsearch": "up" if es_ok else "down",
        "redis": "up" if redis_ok else "down",
    }


@app.get("/", tags=["Служебные"], summary="Корневой эндпоинт")
async def root() -> dict:
    """Вернуть приветствие и ссылку на документацию.

    Returns:
        Краткая информация о сервисе.
    """
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
    }
