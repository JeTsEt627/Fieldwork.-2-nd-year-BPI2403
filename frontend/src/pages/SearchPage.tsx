// Страница поиска: поле ввода (FE-04), карточки результатов (FE-05),
// подсветка (FE-06), пагинация (FE-07), пустое состояние (FE-08).

import { useCallback, useState } from "react";

import { SearchBar } from "../components/SearchBar";
import { SearchResults } from "../components/SearchResults";
import { ApiError, search } from "../services/api";
import type { SearchResponse } from "../types";

const PAGE_SIZE = 10;

export function SearchPage() {
  const [query, setQuery] = useState("");
  const [response, setResponse] = useState<SearchResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /** Выполнить запрос к API для конкретной страницы. */
  const runSearch = useCallback(async (q: string, page: number) => {
    setLoading(true);
    setError(null);
    try {
      const data = await search(q, page, PAGE_SIZE);
      setResponse(data);
    } catch (err) {
      const message =
        err instanceof ApiError ? err.message : "Ошибка выполнения поиска";
      setError(message);
      setResponse(null);
    } finally {
      setLoading(false);
    }
  }, []);

  const onSearch = useCallback(
    (q: string) => {
      setQuery(q);
      void runSearch(q, 1);
    },
    [runSearch],
  );

  const onPageChange = useCallback(
    (page: number) => {
      void runSearch(query, page);
      window.scrollTo({ top: 0, behavior: "smooth" });
    },
    [query, runSearch],
  );

  return (
    <div className="page">
      <section className="panel">
        <h2>Поиск по базе знаний</h2>
        <SearchBar loading={loading} onSearch={onSearch} />
      </section>

      <SearchResults
        response={response}
        loading={loading}
        error={error}
        onPageChange={onPageChange}
      />
    </div>
  );
}
