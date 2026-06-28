// Список загруженных документов: название, дата загрузки, статус (FE-03).

import { useCallback, useEffect, useState } from "react";

import { deleteDocument, listDocuments } from "../services/api";
import type { DocumentItem } from "../types";
import { StatusBadge } from "./StatusBadge";

interface DocumentListProps {
  /** Счётчик-триггер для перезагрузки списка (меняется после загрузки). */
  refreshKey: number;
}

/** Отформатировать дату ISO в читаемый вид. */
function formatDate(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso;
  return date.toLocaleString("ru-RU", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

/** Перевести размер в байтах в КБ/МБ. */
function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} Б`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} КБ`;
  return `${(bytes / 1024 / 1024).toFixed(1)} МБ`;
}

export function DocumentList({ refreshKey }: DocumentListProps) {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await listDocuments(100, 0);
      setDocuments(data.items);
    } catch {
      setError("Не удалось загрузить список документов");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load, refreshKey]);

  const onDelete = useCallback(
    async (id: string) => {
      try {
        await deleteDocument(id);
        setDocuments((prev) => prev.filter((doc) => doc.id !== id));
      } catch {
        setError("Не удалось удалить документ");
      }
    },
    [],
  );

  return (
    <section className="doclist">
      <div className="doclist__header">
        <h2>Загруженные документы</h2>
        <button className="btn btn--ghost" onClick={() => void load()}>
          Обновить
        </button>
      </div>

      {error && <p className="error-text">{error}</p>}
      {loading && documents.length === 0 && <p>Загрузка...</p>}
      {!loading && documents.length === 0 && !error && (
        <p className="muted">Пока нет загруженных документов.</p>
      )}

      {documents.length > 0 && (
        <div className="doclist__table-wrap">
          <table className="doclist__table">
            <thead>
              <tr>
                <th>Название</th>
                <th>Дата загрузки</th>
                <th>Размер</th>
                <th>Статус</th>
                <th aria-label="Действия" />
              </tr>
            </thead>
            <tbody>
              {documents.map((doc) => (
                <tr key={doc.id}>
                  <td className="doclist__name" title={doc.file_name}>
                    {doc.file_name}
                  </td>
                  <td>{formatDate(doc.created_at)}</td>
                  <td>{formatSize(doc.file_size)}</td>
                  <td>
                    <StatusBadge status={doc.status} />
                    {doc.status === "error" && doc.error_message && (
                      <span
                        className="doclist__error"
                        title={doc.error_message}
                      >
                        {" "}
                        ⓘ
                      </span>
                    )}
                  </td>
                  <td>
                    <button
                      className="btn btn--danger btn--small"
                      onClick={() => void onDelete(doc.id)}
                    >
                      Удалить
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
