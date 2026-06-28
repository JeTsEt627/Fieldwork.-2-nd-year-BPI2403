# Backend — Интеллектуальная поисковая система по базе знаний

REST API на FastAPI для загрузки документов (PDF/DOCX), извлечения текста,
индексации в Elasticsearch и полнотекстового поиска с подсветкой совпадений.

## Технологический стек

- **Python 3.12** + **FastAPI** — веб-фреймворк и асинхронный API
- **PostgreSQL** (SQLAlchemy 2.0, asyncpg) — метаданные документов и история поиска
- **Elasticsearch 8** — полнотекстовый поиск с русскоязычным анализатором
- **Redis** — кеширование частых запросов (TTL = 5 минут)
- **pdfplumber** / **python-docx** — извлечение текста
- **pytest** — юнит- и интеграционные тесты

## Структура

```
backend/
├── app/
│   ├── api/          # HTTP-эндпоинты (documents, search)
│   ├── core/         # Конфигурация, БД, клиенты, исключения, логирование
│   ├── models/       # SQLAlchemy-модели (Document, SearchHistory)
│   ├── schemas/      # Pydantic-схемы запросов/ответов
│   ├── services/     # Бизнес-логика (парсинг, чанкинг, индексация, поиск, кеш)
│   └── main.py       # Точка входа, сборка приложения
├── tests/            # Юнит- и интеграционные тесты
├── requirements.txt
└── Dockerfile
```

## Реализованные требования (BE)

| ID    | Описание                                                       | Где |
|-------|----------------------------------------------------------------|-----|
| BE-01 | `POST /api/v1/documents/upload`                                | `api/documents.py` |
| BE-02 | Валидация формата (PDF/DOCX) и размера (≤ 20 МБ) → HTTP 400     | `services/file_validation.py` |
| BE-03 | Генерация UUID для каждого документа                           | `models/document.py` |
| BE-04 | Извлечение текста (pdfplumber / python-docx)                   | `services/document_parser.py` |
| BE-05 | Чанкинг по 1000 символов с перекрытием 100                     | `services/chunker.py` |
| BE-06 | Индекс `documents` с русскоязычным анализатором                | `services/elasticsearch_service.py` |
| BE-07 | Индексация чанков с метаданными                               | `services/elasticsearch_service.py` |
| BE-08 | `GET /api/v1/search?q={query}` через `multi_match`             | `api/search.py` |
| BE-09 | JSON-ответ: `chunk_id, file_name, page, text, score`          | `schemas/search.py` |
| BE-10 | Кеширование запросов в Redis (TTL = 5 мин)                     | `services/cache.py` |

Документация OpenAPI 3.0 — Swagger UI по адресу `/docs`.

## Запуск

### Через Docker Compose (рекомендуется)

Из корня репозитория:

```bash
cp .env.example .env
docker compose up --build
```

API будет доступен на http://localhost:8000, Swagger — http://localhost:8000/docs

### Локально (для разработки)

Требуются запущенные PostgreSQL, Elasticsearch и Redis (можно поднять только их
через `docker compose up postgres elasticsearch redis`).

```bash
cd backend
python -m venv .venv
.venv/Scripts/activate        # Windows
# source .venv/bin/activate   # Linux/macOS
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Тесты

```bash
cd backend
pip install -r requirements.txt
pytest                          # запуск всех тестов
pytest --cov=app --cov-report=term-missing   # с покрытием (нужен pytest-cov)
```

## Основные эндпоинты

| Метод   | Путь                          | Назначение                          |
|---------|-------------------------------|-------------------------------------|
| POST    | `/api/v1/documents/upload`    | Загрузка и индексация документа     |
| GET     | `/api/v1/documents`           | Список загруженных документов       |
| GET     | `/api/v1/documents/{id}`      | Метаданные документа                |
| DELETE  | `/api/v1/documents/{id}`      | Удаление документа и его чанков     |
| GET     | `/api/v1/search?q=...`        | Полнотекстовый поиск                |
| GET     | `/api/v1/search/history`      | История поисковых запросов          |
| GET     | `/health`                     | Состояние сервиса и зависимостей    |
