# Инструменты тестирования (QA)

Здесь собраны инструменты тестировщика, не относящиеся к юнит-тестам бэкенда
(те лежат в `backend/tests/`).

| Задача | Файл/каталог | Назначение |
|--------|--------------|-----------|
| QA-03 | `../backend/tests/fixtures/generate_fixtures.py` | Генерация набора тестовых документов |
| QA-04 | `load/locustfile.py` | Нагрузочное тестирование поиска |
| QA-05 | `precision_at_3.py`, `reference_queries.json` | Оценка качества поиска Precision@3 |

## Установка зависимостей

```bash
pip install -r qa/requirements.txt
```

## QA-04 — Нагрузочное тестирование (Locust)

Имитация 50 одновременных пользователей, выполняющих поиск, с отчётом о
времени отклика.

```bash
locust -f qa/load/locustfile.py --host http://localhost:8000 \
    --users 50 --spawn-rate 10 --run-time 2m --headless \
    --html qa/load/report.html
```

После прогона:
- сводка по времени отклика (min / max / median / p95) выводится в консоль;
- подробный HTML-отчёт — в `qa/load/report.html`.

Веб-интерфейс (ручное управление нагрузкой) — без флага `--headless`:
```bash
locust -f qa/load/locustfile.py --host http://localhost:8000
# открыть http://localhost:8089
```

## QA-05 — Оценка качества поиска (Precision@3)

Проверяет для 10 эталонных запросов, что нужный документ входит в топ-3 выдачи.
Предварительно загрузите документы (`./init.sh`).

```bash
python qa/precision_at_3.py
# или: API_URL=http://localhost:8000 python qa/precision_at_3.py
```

Результат — таблица в консоли и файл `qa/precision_report.md`.
Эталонные запросы и ожидаемые документы заданы в `reference_queries.json`
и соответствуют файлам, которые загружает `init.sh`.
