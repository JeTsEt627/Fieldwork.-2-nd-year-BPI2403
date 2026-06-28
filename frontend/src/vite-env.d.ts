/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Базовый путь REST API (по умолчанию /api/v1). */
  readonly VITE_API_BASE?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
