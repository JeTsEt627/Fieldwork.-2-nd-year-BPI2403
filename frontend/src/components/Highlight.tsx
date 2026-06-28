// Подсветка совпадений жёлтым фоном (FE-06).
//
// Бэкенд (Elasticsearch) возвращает поле highlight с фрагментом, в котором
// совпадения обёрнуты в <em>...</em> — с учётом морфологии русского языка.
// Если highlight отсутствует, выполняем подсветку слов запроса на стороне
// клиента. В обоих случаях текст рендерится как React-узлы (без
// dangerouslySetInnerHTML), поэтому XSS невозможен.

import type { ReactElement } from "react";

interface HighlightProps {
  /** Полный текст фрагмента. */
  text: string;
  /** Готовый фрагмент с тегами <em> из Elasticsearch (предпочтительно). */
  highlight?: string | null;
  /** Поисковый запрос — для клиентской подсветки, если highlight нет. */
  query?: string;
}

/** Экранировать спецсимволы регулярного выражения. */
function escapeRegExp(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

/** Разобрать строку с тегами <em>…</em> в массив React-узлов. */
function renderEsHighlight(fragment: string): ReactElement[] {
  const parts = fragment.split(/<em>(.*?)<\/em>/g);
  // Чётные индексы — обычный текст, нечётные — подсвеченные совпадения.
  return parts.map((part, index) =>
    index % 2 === 1 ? (
      <mark key={index}>{part}</mark>
    ) : (
      <span key={index}>{part}</span>
    ),
  );
}

/** Подсветить слова запроса в произвольном тексте на стороне клиента. */
function renderClientHighlight(text: string, query: string): ReactElement[] {
  const terms = query
    .trim()
    .split(/\s+/)
    .filter((term) => term.length > 1)
    .map(escapeRegExp);

  if (terms.length === 0) {
    return [<span key="0">{text}</span>];
  }

  const regex = new RegExp(`(${terms.join("|")})`, "gi");
  // split с одной группой захвата помещает совпадения на нечётные индексы.
  const parts = text.split(regex);
  return parts.map((part, index) =>
    index % 2 === 1 ? (
      <mark key={index}>{part}</mark>
    ) : (
      <span key={index}>{part}</span>
    ),
  );
}

/** Текстовый фрагмент с жёлтой подсветкой найденных слов. */
export function Highlight({ text, highlight, query }: HighlightProps) {
  if (highlight) {
    return <>{renderEsHighlight(highlight)}</>;
  }
  if (query) {
    return <>{renderClientHighlight(text, query)}</>;
  }
  return <>{text}</>;
}
