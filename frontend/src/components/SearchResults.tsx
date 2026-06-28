// Блок вывода результатов поиска: карточки (FE-05), пустое состояние (FE-08),
// сводка и пагинация (FE-07).

import type { SearchResponse } from "../types";
import { Pagination } from "./Pagination";
import { ResultCard } from "./ResultCard";

interface SearchResultsProps {
  response: SearchResponse | null;
  loading: boolean;
  error: string | null;
  onPageChange: (page: number) => void;
}

export function SearchResults({
  response,
  loading,
  error,
  onPageChange,
}: SearchResultsProps) {
  if (loading) {
    return <p className="results__status">Идёт поиск...</p>;
  }

  if (error) {
    return <p className="error-text">{error}</p>;
  }

  if (!response) {
    return null;
  }

  // Пустая выдача (FE-08).
  if (response.total === 0) {
    return (
      <p className="results__empty">
        По вашему запросу ничего не найдено. Попробуйте изменить формулировку.
      </p>
    );
  }

  return (
    <div className="results">
      <p className="results__summary">
        Найдено результатов: <strong>{response.total}</strong> за{" "}
        {response.took_ms} мс
        {response.from_cache && (
          <span className="results__cache" title="Ответ получен из кеша Redis">
            {" "}
            · из кеша
          </span>
        )}
      </p>

      <div className="results__list">
        {response.results.map((item) => (
          <ResultCard key={item.chunk_id} item={item} query={response.query} />
        ))}
      </div>

      <Pagination
        page={response.page}
        pageSize={response.page_size}
        total={response.total}
        onChange={onPageChange}
      />
    </div>
  );
}
