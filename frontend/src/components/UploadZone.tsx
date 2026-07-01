// Зона загрузки документов с Drag-and-Drop и множественной загрузкой (FE-01),
// отображением прогресса/статуса каждого файла (FE-02).

import { type DragEvent, useCallback, useRef, useState } from "react";

import { ApiError, uploadDocument } from "../services/api";
import type { UploadTask } from "../types";
import { StatusBadge } from "./StatusBadge";

const ALLOWED_EXTENSIONS = ["pdf", "docx"];

interface UploadZoneProps {
  /** Вызывается после завершения загрузки (успешной или с ошибкой). */
  onUploaded?: () => void;
}

function getExtension(name: string): string {
  const dot = name.lastIndexOf(".");
  return dot >= 0 ? name.slice(dot + 1).toLowerCase() : "";
}

/** Сгенерировать локальный идентификатор задачи загрузки. */
function makeTaskId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

export function UploadZone({ onUploaded }: UploadZoneProps) {
  const [isDragOver, setIsDragOver] = useState(false);
  const [tasks, setTasks] = useState<UploadTask[]>([]);
  const inputRef = useRef<HTMLInputElement>(null);

  /** Обновить состояние одной задачи по идентификатору. */
  const updateTask = useCallback((id: string, patch: Partial<UploadTask>) => {
    setTasks((prev) =>
      prev.map((task) => (task.id === id ? { ...task, ...patch } : task)),
    );
  }, []);

  /** Загрузить один файл и отразить его статус (FE-02). */
  const uploadOne = useCallback(
    async (file: File) => {
      const id = makeTaskId();
      const extension = getExtension(file.name);

      setTasks((prev) => [
        { id, fileName: file.name, status: "uploading" },
        ...prev,
      ]);

      // Клиентская валидация формата до отправки на сервер.
      if (!ALLOWED_EXTENSIONS.includes(extension)) {
        updateTask(id, {
          status: "error",
          message: "Допустимы только файлы PDF и DOCX",
        });
        return;
      }

      try {
        // Переход в «Индексация...» — сервер парсит и индексирует файл.
        updateTask(id, { status: "indexing" });
        const result = await uploadDocument(file);
        updateTask(id, {
          status: "done",
          message: `${result.page_count} стр., ${result.chunk_count} фрагм.`,
        });
        onUploaded?.();
      } catch (error) {
        const message =
          error instanceof ApiError
            ? error.message
            : "Не удалось загрузить файл";
        updateTask(id, { status: "error", message });
      }
    },
    [onUploaded, updateTask],
  );

  /** Обработать набор выбранных/перетащенных файлов. */
  const handleFiles = useCallback(
    (fileList: FileList | null) => {
      if (!fileList) return;
      Array.from(fileList).forEach((file) => void uploadOne(file));
    },
    [uploadOne],
  );

  const onDrop = useCallback(
    (event: DragEvent<HTMLDivElement>) => {
      event.preventDefault();
      setIsDragOver(false);
      handleFiles(event.dataTransfer.files);
    },
    [handleFiles],
  );

  return (
    <div className="upload">
      <div
        className={`dropzone${isDragOver ? " dropzone--active" : ""}`}
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragOver(true);
        }}
        onDragLeave={() => setIsDragOver(false)}
        onDrop={onDrop}
        onClick={() => inputRef.current?.click()}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") inputRef.current?.click();
        }}
      >
        <input
          ref={inputRef}
          type="file"
          multiple
          accept=".pdf,.docx"
          hidden
          onChange={(e) => {
            handleFiles(e.target.files);
            e.target.value = "";
          }}
        />
        <p className="dropzone__title">
          Перетащите файлы сюда или нажмите для выбора
        </p>
        <p className="dropzone__hint">Поддерживаются PDF и DOCX (до 20 МБ)</p>
      </div>

      {tasks.length > 0 && (
        <ul className="upload__list">
          {tasks.map((task) => (
            <li key={task.id} className="upload__item">
              <span className="upload__name" title={task.fileName}>
                {task.fileName}
              </span>
              <span className="upload__status">
                {(task.status === "uploading" ||
                  task.status === "indexing") && (
                  <span className="spinner" aria-hidden="true" />
                )}
                <StatusBadge status={task.status} />
              </span>
              {task.message && (
                <span className="upload__message">{task.message}</span>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
