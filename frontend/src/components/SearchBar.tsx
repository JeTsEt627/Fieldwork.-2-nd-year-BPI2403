// Поле ввода поискового запроса с кнопкой «Найти» (FE-04).
// Поиск запускается по кнопке и по нажатию Enter.

import { useState } from "react";

interface SearchBarProps {
  /** Начальное значение поля. */
  initialValue?: string;
  /** Идёт ли поиск (для блокировки кнопки). */
  loading?: boolean;
  /** Колбэк запуска поиска. */
  onSearch: (query: string) => void;
}

export function SearchBar({
  initialValue = "",
  loading = false,
  onSearch,
}: SearchBarProps) {
  const [value, setValue] = useState(initialValue);

  const submit = () => {
    const trimmed = value.trim();
    if (trimmed) {
      onSearch(trimmed);
    }
  };

  return (
    <div className="searchbar">
      <input
        className="searchbar__input"
        type="search"
        placeholder="Введите поисковый запрос..."
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter") submit();
        }}
        aria-label="Поисковый запрос"
        autoFocus
      />
      <button
        className="btn btn--primary"
        onClick={submit}
        disabled={loading || value.trim().length === 0}
      >
        {loading ? "Поиск..." : "Найти"}
      </button>
    </div>
  );
}
