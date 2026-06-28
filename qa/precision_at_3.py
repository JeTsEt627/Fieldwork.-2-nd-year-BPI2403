"""Оценка качества поиска по метрике Precision@3 (QA-05).

Для набора эталонных запросов (``reference_queries.json``) скрипт обращается к
поисковому API и проверяет, входит ли ожидаемый документ в топ-3 результатов.
Итог оформляется в виде таблицы Markdown и сохраняется в файл.

Предварительно документы должны быть загружены в систему (например, через
``init.sh``).

Запуск:
    python qa/precision_at_3.py
    API_URL=http://localhost:8000 python qa/precision_at_3.py
"""

import json
import os
import urllib.parse
import urllib.request

API_URL = os.environ.get("API_URL", "http://localhost:8000")
TOP_K = 3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
QUERIES_PATH = os.path.join(BASE_DIR, "reference_queries.json")
REPORT_PATH = os.path.join(BASE_DIR, "precision_report.md")


def search_top_filenames(query: str, k: int = TOP_K) -> list[str]:
    """Вернуть имена файлов из топ-k результатов поиска по запросу.

    Args:
        query: Поисковый запрос.
        k: Количество результатов (размер выдачи).

    Returns:
        Список имён файлов в порядке релевантности.
    """
    params = urllib.parse.urlencode({"q": query, "page": 1, "page_size": k})
    url = f"{API_URL}/api/v1/search?{params}"
    with urllib.request.urlopen(url, timeout=30) as response:  # noqa: S310
        data = json.loads(response.read().decode("utf-8"))
    return [item["file_name"] for item in data.get("results", [])]


def evaluate() -> None:
    """Прогнать эталонные запросы и сформировать отчёт Precision@3."""
    with open(QUERIES_PATH, encoding="utf-8") as fh:
        queries = json.load(fh)["queries"]

    rows: list[str] = []
    hits = 0

    for entry in queries:
        query = entry["query"]
        expected = entry["expected"]
        try:
            top = search_top_filenames(query)
        except Exception as exc:  # noqa: BLE001
            top = []
            print(f"Ошибка запроса {query!r}: {exc}")

        found = expected in top
        if found:
            hits += 1

        top_display = ", ".join(top) if top else "—"
        rows.append(
            f"| {query} | {expected} | {top_display} | "
            f"{'✓' if found else '✗'} |"
        )

    total = len(queries)
    precision = hits / total if total else 0.0

    lines = [
        "# Оценка качества поиска — Precision@3 (QA-05)",
        "",
        f"API: `{API_URL}` · запросов: {total} · топ-K: {TOP_K}",
        "",
        "| Запрос | Ожидаемый документ | Топ-3 выдачи | Найден |",
        "|--------|--------------------|--------------|--------|",
        *rows,
        "",
        f"**Precision@3 = {hits}/{total} = {precision:.2f}**",
        "",
    ]
    report = "\n".join(lines)

    with open(REPORT_PATH, "w", encoding="utf-8") as fh:
        fh.write(report)

    print(report)
    print(f"\nОтчёт сохранён: {REPORT_PATH}")


if __name__ == "__main__":
    evaluate()
