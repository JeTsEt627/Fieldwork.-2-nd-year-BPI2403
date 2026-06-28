"""Интеграция с Elasticsearch (BE-06, BE-07, BE-08).

Модуль отвечает за:
- создание индекса ``documents`` с русскоязычным анализатором (BE-06);
- индексацию чанков документа с метаданными (BE-07);
- полнотекстовый поиск через ``multi_match`` по полю ``text`` (BE-08).
"""

from typing import Any

from elasticsearch import AsyncElasticsearch, NotFoundError
from elasticsearch.helpers import async_bulk

from app.core.exceptions import SearchServiceError
from app.core.logging_config import get_logger
from app.services.chunker import TextChunk

logger = get_logger(__name__)


# Настройки анализа: кастомный русскоязычный анализатор (BE-06).
# Используются встроенные фильтры Snowball-стеммера и стоп-слов, поэтому
# дополнительные плагины не требуются.
INDEX_SETTINGS: dict[str, Any] = {
    "analysis": {
        "filter": {
            "russian_stop": {"type": "stop", "stopwords": "_russian_"},
            "russian_stemmer": {"type": "stemmer", "language": "russian"},
            "english_stop": {"type": "stop", "stopwords": "_english_"},
            "english_stemmer": {"type": "stemmer", "language": "english"},
        },
        "analyzer": {
            # Основной анализатор для русского текста с поддержкой английских слов.
            "ru_analyzer": {
                "type": "custom",
                "tokenizer": "standard",
                "filter": [
                    "lowercase",
                    "russian_stop",
                    "russian_stemmer",
                    "english_stop",
                    "english_stemmer",
                ],
            }
        },
    }
}

# Маппинг полей индекса (BE-07).
INDEX_MAPPINGS: dict[str, Any] = {
    "properties": {
        "document_id": {"type": "keyword"},
        "chunk_id": {"type": "keyword"},
        "chunk_index": {"type": "integer"},
        "file_name": {
            "type": "text",
            "analyzer": "ru_analyzer",
            "fields": {"keyword": {"type": "keyword", "ignore_above": 512}},
        },
        "page_number": {"type": "integer"},
        "text": {"type": "text", "analyzer": "ru_analyzer"},
    }
}


def build_chunk_id(document_id: str, chunk_index: int) -> str:
    """Сформировать стабильный идентификатор чанка.

    Args:
        document_id: UUID документа.
        chunk_index: Порядковый номер чанка в документе.

    Returns:
        Идентификатор вида ``"<document_id>::<chunk_index>"``.
    """
    return f"{document_id}::{chunk_index}"


class ElasticsearchService:
    """Обёртка над клиентом Elasticsearch для индексации и поиска."""

    def __init__(self, client: AsyncElasticsearch, index_name: str) -> None:
        """Инициализировать сервис.

        Args:
            client: Асинхронный клиент Elasticsearch.
            index_name: Имя индекса для хранения чанков.
        """
        self._client = client
        self._index = index_name

    async def ping(self) -> bool:
        """Проверить доступность кластера Elasticsearch.

        Returns:
            ``True``, если кластер отвечает, иначе ``False``.
        """
        try:
            return await self._client.ping()
        except Exception:  # noqa: BLE001 - для health-check достаточно факта ошибки
            return False

    async def ensure_index(self) -> None:
        """Создать индекс с анализатором и маппингом, если он не существует (BE-06).

        Raises:
            SearchServiceError: Если создать индекс не удалось.
        """
        try:
            exists = await self._client.indices.exists(index=self._index)
            if exists:
                logger.info("Индекс '%s' уже существует", self._index)
                return
            await self._client.indices.create(
                index=self._index,
                settings=INDEX_SETTINGS,
                mappings=INDEX_MAPPINGS,
            )
            logger.info("Создан индекс '%s'", self._index)
        except Exception as exc:
            raise SearchServiceError(
                f"Не удалось создать индекс '{self._index}': {exc}"
            ) from exc

    async def index_chunks(
        self,
        document_id: str,
        file_name: str,
        chunks: list[TextChunk],
    ) -> int:
        """Проиндексировать чанки документа (BE-07).

        Каждый чанк сохраняется отдельным документом Elasticsearch с
        метаданными: ``file_name``, ``page_number``, ``chunk_id``, ``text``.

        Args:
            document_id: UUID документа.
            file_name: Имя файла-источника.
            chunks: Список чанков для индексации.

        Returns:
            Количество успешно проиндексированных чанков.

        Raises:
            SearchServiceError: Если массовая индексация завершилась ошибкой.
        """
        if not chunks:
            return 0

        actions = []
        for chunk in chunks:
            chunk_id = build_chunk_id(document_id, chunk.chunk_index)
            actions.append(
                {
                    "_index": self._index,
                    "_id": chunk_id,
                    "_source": {
                        "document_id": document_id,
                        "chunk_id": chunk_id,
                        "chunk_index": chunk.chunk_index,
                        "file_name": file_name,
                        "page_number": chunk.page_number,
                        "text": chunk.text,
                    },
                }
            )

        try:
            success, errors = await async_bulk(
                self._client, actions, refresh="wait_for"
            )
        except Exception as exc:
            raise SearchServiceError(f"Ошибка индексации чанков: {exc}") from exc

        if errors:
            logger.error("Ошибки при индексации чанков: %s", errors)
            raise SearchServiceError("Часть чанков не удалось проиндексировать")

        logger.info(
            "Проиндексировано %d чанков документа %s", success, document_id
        )
        return success

    async def search(
        self,
        query: str,
        page: int = 1,
        page_size: int = 10,
    ) -> dict[str, Any]:
        """Выполнить полнотекстовый поиск (BE-08).

        Используется запрос ``multi_match`` по полю ``text`` (основное) с
        дополнительным учётом имени файла. Совпадения подсвечиваются.

        Args:
            query: Поисковый запрос.
            page: Номер страницы результатов (начиная с 1).
            page_size: Количество результатов на странице.

        Returns:
            Словарь с ключами ``total`` (всего найдено), ``took_ms`` (время
            выполнения) и ``results`` (список найденных фрагментов согласно
            BE-09).

        Raises:
            SearchServiceError: Если запрос к Elasticsearch завершился ошибкой.
        """
        from_offset = max(page - 1, 0) * page_size

        es_query = {
            "multi_match": {
                "query": query,
                "fields": ["text^3", "file_name"],
                "type": "best_fields",
                "fuzziness": "AUTO",
            }
        }
        highlight = {
            "fields": {"text": {"number_of_fragments": 1, "fragment_size": 300}},
            "pre_tags": ["<em>"],
            "post_tags": ["</em>"],
        }

        try:
            response = await self._client.search(
                index=self._index,
                query=es_query,
                highlight=highlight,
                from_=from_offset,
                size=page_size,
            )
        except NotFoundError as exc:
            # Индекс ещё не создан — поиск возвращает пустой результат.
            logger.warning("Индекс '%s' не найден при поиске", self._index)
            raise SearchServiceError("Индекс документов не найден") from exc
        except Exception as exc:
            raise SearchServiceError(f"Ошибка поиска: {exc}") from exc

        return self._format_response(response)

    @staticmethod
    def _format_response(response: dict[str, Any]) -> dict[str, Any]:
        """Преобразовать ответ Elasticsearch к формату BE-09.

        Args:
            response: Сырой ответ клиента Elasticsearch.

        Returns:
            Нормализованный словарь с результатами поиска.
        """
        hits = response.get("hits", {})
        total = hits.get("total", {})
        total_value = total.get("value", 0) if isinstance(total, dict) else total

        results = []
        for hit in hits.get("hits", []):
            source = hit.get("source", hit.get("_source", {}))
            highlight_fragments = hit.get("highlight", {}).get("text", [])
            results.append(
                {
                    "chunk_id": source.get("chunk_id", hit.get("_id", "")),
                    "file_name": source.get("file_name", ""),
                    "page": source.get("page_number", 0),
                    "text": source.get("text", ""),
                    "score": hit.get("_score") or 0.0,
                    "highlight": highlight_fragments[0]
                    if highlight_fragments
                    else None,
                }
            )

        return {
            "total": total_value,
            "took_ms": response.get("took", 0),
            "results": results,
        }

    async def delete_document(self, document_id: str) -> int:
        """Удалить все чанки документа из индекса.

        Args:
            document_id: UUID документа.

        Returns:
            Количество удалённых чанков.

        Raises:
            SearchServiceError: Если удаление завершилось ошибкой.
        """
        try:
            response = await self._client.delete_by_query(
                index=self._index,
                query={"term": {"document_id": document_id}},
                refresh=True,
                ignore_unavailable=True,
            )
        except Exception as exc:
            raise SearchServiceError(f"Ошибка удаления документа: {exc}") from exc
        return response.get("deleted", 0)
