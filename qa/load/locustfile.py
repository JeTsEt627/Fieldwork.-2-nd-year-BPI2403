"""Нагрузочный тест поиска (QA-04).

Имитирует одновременных пользователей, выполняющих поисковые запросы к
эндпоинту ``GET /api/v1/search``. Locust собирает статистику времени отклика
и формирует отчёт.

Запуск (50 пользователей, headless, HTML-отчёт):

    locust -f qa/load/locustfile.py --host http://localhost:8000 \
        --users 50 --spawn-rate 10 --run-time 2m --headless \
        --html qa/load/report.html

Или с веб-интерфейсом (http://localhost:8089):

    locust -f qa/load/locustfile.py --host http://localhost:8000
"""

import random

from locust import HttpUser, between, task

# Набор запросов, имитирующих реальную нагрузку.
SEARCH_QUERIES = [
    "машинное обучение",
    "нейронная сеть",
    "attention transformer",
    "градиентный спуск",
    "обработка естественного языка",
    "свёрточная сеть",
    "классификация изображений",
    "векторное представление слов",
    "оптимизация Adam",
    "сегментация изображений",
]


class SearchUser(HttpUser):
    """Виртуальный пользователь, выполняющий поисковые запросы."""

    # Пауза между запросами одного пользователя (имитация «think time»).
    wait_time = between(0.5, 2.0)

    @task(4)
    def search(self) -> None:
        """Выполнить случайный поисковый запрос."""
        query = random.choice(SEARCH_QUERIES)
        # name группирует метрики по эндпоинту, а не по каждому query.
        self.client.get(
            "/api/v1/search",
            params={"q": query, "page": 1, "page_size": 10},
            name="GET /api/v1/search",
        )

    @task(1)
    def search_second_page(self) -> None:
        """Изредка запрашивать вторую страницу результатов."""
        query = random.choice(SEARCH_QUERIES)
        self.client.get(
            "/api/v1/search",
            params={"q": query, "page": 2, "page_size": 10},
            name="GET /api/v1/search?page=2",
        )
