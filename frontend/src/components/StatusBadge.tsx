// Бейдж статуса документа/загрузки (FE-02, FE-03).

import type { DocumentStatus } from "../types";

type AnyStatus = DocumentStatus | "uploading" | "indexing" | "done" | "error";

// Человекочитаемые подписи статусов на русском.
const STATUS_LABELS: Record<string, string> = {
  uploading: "Загрузка...",
  indexing: "Индексация...",
  ready: "Готово",
  done: "Готово",
  error: "Ошибка",
};

interface StatusBadgeProps {
  status: AnyStatus;
}

/** Цветной бейдж с подписью статуса. */
export function StatusBadge({ status }: StatusBadgeProps) {
  const label = STATUS_LABELS[status] ?? status;
  return <span className={`badge badge--${status}`}>{label}</span>;
}
