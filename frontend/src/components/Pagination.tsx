// Пагинация результатов поиска по 10 на страницу (FE-07).

interface PaginationProps {
  page: number;
  pageSize: number;
  total: number;
  onChange: (page: number) => void;
}

export function Pagination({
  page,
  pageSize,
  total,
  onChange,
}: PaginationProps) {
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  if (totalPages <= 1) return null;

  return (
    <nav className="pagination" aria-label="Навигация по страницам">
      <button
        className="btn btn--ghost btn--small"
        onClick={() => onChange(page - 1)}
        disabled={page <= 1}
      >
        ← Назад
      </button>
      <span className="pagination__info">
        Страница {page} из {totalPages}
      </span>
      <button
        className="btn btn--ghost btn--small"
        onClick={() => onChange(page + 1)}
        disabled={page >= totalPages}
      >
        Вперёд →
      </button>
    </nav>
  );
}
