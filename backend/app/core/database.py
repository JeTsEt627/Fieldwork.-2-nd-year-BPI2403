"""Подключение к PostgreSQL через асинхронный движок SQLAlchemy 2.0."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


class Base(DeclarativeBase):
    """Базовый класс для всех ORM-моделей проекта."""


# echo=settings.debug выводит SQL-запросы в лог в режиме отладки.
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,
)

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI-зависимость, выдающая сессию БД на время запроса.

    Сессия автоматически закрывается по завершении запроса. При исключении
    выполняется откат транзакции.

    Yields:
        Активная асинхронная сессия SQLAlchemy.
    """
    async with async_session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


async def init_models() -> None:
    """Создать таблицы в БД на основе метаданных моделей.

    Используется при старте приложения для прототипа. В продакшене
    предпочтительнее миграции (Alembic).
    """
    # Импорт моделей нужен, чтобы они зарегистрировались в Base.metadata.
    from app import models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
