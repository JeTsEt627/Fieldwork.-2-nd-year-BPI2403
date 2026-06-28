# Многоэтапная сборка: компиляция статики Node + раздача через Nginx (DO-02).

# --- Этап сборки ---
FROM node:20-alpine AS build

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# --- Этап раздачи ---
FROM nginx:1.27-alpine

# SPA-конфигурация Nginx с проксированием /api на бэкенд.
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
