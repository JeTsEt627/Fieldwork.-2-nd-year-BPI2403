// Типы данных, соответствующие схемам ответов бэкенда.

/** Статус обработки документа (совпадает с DocumentStatus на бэкенде). */
export type DocumentStatus = "uploading" | "indexing" | "ready" | "error";

/** Метаданные загруженного документа (GET /documents). */
export interface DocumentItem {
  id: string;
  file_name: string;
  content_type: string;
  file_size: number;
  status: DocumentStatus;
  chunk_count: number;
  page_count: number;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

/** Ответ на загрузку документа (POST /documents/upload). */
export interface DocumentUploadResponse {
  id: string;
  file_name: string;
  status: DocumentStatus;
  chunk_count: number;
  page_count: number;
  message: string;
}

/** Список документов с пагинацией. */
export interface DocumentListResponse {
  total: number;
  items: DocumentItem[];
}

/** Один результат поиска — фрагмент документа (BE-09). */
export interface SearchResultItem {
  chunk_id: string;
  file_name: string;
  page: number;
  text: string;
  score: number;
  highlight: string | null;
}

/** Полный ответ поискового эндпоинта. */
export interface SearchResponse {
  query: string;
  total: number;
  page: number;
  page_size: number;
  took_ms: number;
  from_cache: boolean;
  results: SearchResultItem[];
}

/**
 * Локальное состояние загрузки одного файла в UI (FE-02).
 * Состояния: загрузка, индексация, готово, ошибка.
 */
export interface UploadTask {
  id: string;
  fileName: string;
  status: "uploading" | "indexing" | "done" | "error";
  message?: string;
}
