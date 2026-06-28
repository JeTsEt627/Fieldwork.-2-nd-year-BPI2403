// Сервисный слой: запросы к REST API бэкенда.
//
// Базовый путь относительный (/api/v1): в разработке его проксирует Vite,
// в продакшене — Nginx. При необходимости можно переопределить через
// переменную окружения VITE_API_BASE.

import type {
  DocumentListResponse,
  DocumentUploadResponse,
  SearchResponse,
} from "../types";

const API_BASE = import.meta.env.VITE_API_BASE ?? "/api/v1";

/** Ошибка обращения к API с человекочитаемым описанием. */
export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

/** Разобрать ответ: при ошибке — извлечь поле detail и бросить ApiError. */
async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let detail = `Ошибка запроса (${response.status})`;
    try {
      const body = await response.json();
      if (body?.detail) {
        detail =
          typeof body.detail === "string"
            ? body.detail
            : JSON.stringify(body.detail);
      }
    } catch {
      // тело не JSON — оставляем дефолтное сообщение
    }
    throw new ApiError(response.status, detail);
  }
  return (await response.json()) as T;
}

/**
 * Загрузить документ на сервер (BE-01).
 *
 * @param file Файл PDF или DOCX.
 * @returns Информация о созданном и проиндексированном документе.
 */
export async function uploadDocument(
  file: File,
): Promise<DocumentUploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE}/documents/upload`, {
    method: "POST",
    body: formData,
  });
  return handleResponse<DocumentUploadResponse>(response);
}

/**
 * Получить список загруженных документов (FE-03).
 *
 * @param limit Размер страницы.
 * @param offset Смещение.
 */
export async function listDocuments(
  limit = 50,
  offset = 0,
): Promise<DocumentListResponse> {
  const response = await fetch(
    `${API_BASE}/documents?limit=${limit}&offset=${offset}`,
  );
  return handleResponse<DocumentListResponse>(response);
}

/** Удалить документ по идентификатору. */
export async function deleteDocument(id: string): Promise<void> {
  const response = await fetch(`${API_BASE}/documents/${id}`, {
    method: "DELETE",
  });
  if (!response.ok && response.status !== 204) {
    await handleResponse(response);
  }
}

/**
 * Выполнить полнотекстовый поиск (BE-08).
 *
 * @param query Поисковый запрос.
 * @param page Номер страницы (с 1).
 * @param pageSize Результатов на странице.
 */
export async function search(
  query: string,
  page = 1,
  pageSize = 10,
): Promise<SearchResponse> {
  const params = new URLSearchParams({
    q: query,
    page: String(page),
    page_size: String(pageSize),
  });
  const response = await fetch(`${API_BASE}/search?${params.toString()}`);
  return handleResponse<SearchResponse>(response);
}
