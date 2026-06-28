import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Адрес бэкенда для прокси в режиме разработки.
// В продакшене запросы к /api проксирует Nginx (см. nginx.conf).
const backendUrl = process.env.VITE_BACKEND_URL || "http://localhost:8000";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: true,
    proxy: {
      "/api": {
        target: backendUrl,
        changeOrigin: true,
      },
    },
  },
});
