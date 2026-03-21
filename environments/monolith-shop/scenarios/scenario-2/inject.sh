#!/bin/sh
# сценарий 2: ломаем конфигурацию Nginx
# меняем порт бэкенда на несуществующий — все запросы вернут 502

PROJECT=${COMPOSE_PROJECT_NAME:-prodpolygon}

echo "Breaking nginx configuration..."
docker exec "${PROJECT}-nginx-1" sh -c \
  "sed -i 's/proxy_pass http:\/\/backend:5000/proxy_pass http:\/\/backend:9999/' \
  /etc/nginx/conf.d/default.conf && nginx -s reload" 2>/dev/null || \
docker exec "${PROJECT}_nginx_1" sh -c \
  "sed -i 's/proxy_pass http:\/\/backend:5000/proxy_pass http:\/\/backend:9999/' \
  /etc/nginx/conf.d/default.conf && nginx -s reload" 2>/dev/null

echo "Done. Nginx now proxies to wrong port."