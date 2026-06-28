# Интеллектуальная поисковая система по внутренней базе знаний университета

Веб-приложение для загрузки документов (PDF/DOCX), извлечения текста,
полнотекстового поиска по ним через Elasticsearch с подсветкой совпадений
и сохранением истории запросов.

Учебная практика, направление 09.03.04 «Программная инженерия» (БПИ24).

## Архитектура

Микросервисная архитектура, запускается одной командой через Docker Compose.

| Сервис | Технологии | Порт | Назначение |
|--------|-----------|------|-----------|
| `app` | Python 3.12, FastAPI | 8000 | REST API, парсинг, индексация, поиск |
| `front` | React + TypeScript, Nginx | 3000 | Веб-интерфейс |
| `postgres` | PostgreSQL 16 | 5432 | Метаданные документов, история поиска |
| `elasticsearch` | Elasticsearch 8 | 9200 | Полнотекстовый поиск (рус. анализатор) |
| `redis` | Redis 7 | 6379 | Кеш частых запросов (TTL 5 мин) |
| `prometheus` | Prometheus | 9090 | Сбор метрик |
| `grafana` | Grafana | 3001 | Дашборд мониторинга |

```
/
├── backend/                # FastAPI-приложение (см. backend/README.md)
│   ├── app/                # api, core, models, schemas, services, main.py
│   ├── tests/              # юнит- и интеграционные тесты (pytest)
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/               # React + TypeScript + Vite
│   ├── src/                # components, pages, services, App.tsx
│   ├── package.json
│   ├── nginx.conf
│   └── Dockerfile
├── monitoring/             # Prometheus + Grafana (DO-06)
│   ├── prometheus.yml
│   └── grafana/provisioning/
├── docker-compose.yml      # Запуск всего стека
├── .env.example            # Шаблон переменных окружения (DO-04)
├── .github/workflows/ci.yml # CI/CD (DO-05)
├── init.sh                 # Загрузка 10 тестовых PDF (DO-07)
└── README.md
```

## Быстрый старт

Требуется установленный Docker и Docker Compose.

```bash
# 1. Создать файл окружения из шаблона и при необходимости отредактировать
cp .env.example .env

# 2. Собрать и запустить весь стек
docker compose up --build
```

После старта доступны:

- **Веб-интерфейс**: http://localhost:3000
- **API (Swagger UI)**: http://localhost:8000/docs
- **Grafana** (дашборд мониторинга): http://localhost:3001 (логин/пароль из `.env`)
- **Prometheus**: http://localhost:9090

### Загрузка тестовых данных

После запуска стека можно наполнить систему 10 открытыми PDF-лекциями:

```bash
./init.sh
# или, если API на другом хосте:
API_URL=http://localhost:8000 ./init.sh
```

## Разработка без Docker

**Бэкенд** (нужны запущенные PostgreSQL, Elasticsearch, Redis — можно поднять
только их: `docker compose up postgres elasticsearch redis`):

```bash
cd backend
python -m venv .venv && .venv/Scripts/activate   # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Фронтенд**:

```bash
cd frontend
npm install
npm run dev          # http://localhost:5173, проксирует /api на :8000
```

## Тестирование

```bash
cd backend
pytest --cov=app --cov-report=term-missing   # юнит-тесты + покрытие
```

## CI/CD (DO-05)

GitHub Actions (`.github/workflows/ci.yml`) при пуше в `main` и в пул-реквестах:

1. **backend** — линтер `ruff` + тесты `pytest` с покрытием;
2. **frontend** — линтер `eslint` + сборка `vite build`;
3. **build-images** — при успехе на `main` собирает Docker-образы.

> Для шага `npm ci` в репозитории должен быть закоммичен `frontend/package-lock.json`
> (создаётся командой `npm install`).

## Мониторинг (DO-06)

Бэкенд экспортирует метрики Prometheus по адресу `/metrics`. Prometheus собирает
их, Grafana отображает преднастроенный дашборд «Поисковая система — мониторинг»
с метриками: количество запросов к `/search`, среднее время ответа, разбивка
по эндпоинтам и статусам. Дашборд и источник данных подключаются автоматически.

## Конфигурация

Все настройки и секреты задаются через переменные окружения (файл `.env`,
шаблон — `.env.example`). Подробное описание параметров — в `backend/README.md`.

## Документация

- API: Swagger UI (`/docs`) и ReDoc (`/redoc`) — OpenAPI 3.0.
- Бэкенд: [backend/README.md](backend/README.md).
