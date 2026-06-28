// Карточка одного результата поиска (FE-05): название файла, номер страницы,
// фрагмент текста и оценка релевантности. Подсветка совпадений — FE-06.

import type { SearchResultItem } from "../types";
import { Highlight } from "./Highlight";

interface ResultCardProps {
  item: SearchResultItem;
  /** Текущий запрос — для клиентской подсветки, если нет highlight от ES. */
  query: string;
}

export function ResultCard({ item, query }: ResultCardProps) {
  return (
    <article className="card">
      <header className="card__header">
        <span className="card__file" title={item.file_name}>
          📄 {item.file_name}
        </span>
        <span className="card__meta">
          <span className="card__page">стр. {item.page}</span>
          <span
            className="card__score"
            title="Оценка релевантности (Elasticsearch)"
          >
            {item.score.toFixed(2)}
          </span>
        </span>
      </header>
      <p className="card__text">
        <Highlight text={item.text} highlight={item.highlight} query={query} />
      </p>
    </article>
  );
}
