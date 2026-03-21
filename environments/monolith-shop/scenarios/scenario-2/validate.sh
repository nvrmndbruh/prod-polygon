#!/bin/sh
# проверяем, что Nginx корректно проксирует на порт 5000

PROJECT=${COMPOSE_PROJECT_NAME:-prodpolygon}

CONFIG=$(docker exec "${PROJECT}-nginx-1" \
  cat /etc/nginx/conf.d/default.conf 2>/dev/null || \
  docker exec "${PROJECT}_nginx_1" \
  cat /etc/nginx/conf.d/default.conf 2>/dev/null)

if echo "$CONFIG" | grep -q "proxy_pass http://backend:5000"; then
  echo "OK: Nginx configuration is correct"
  exit 0
else
  echo "FAIL: Nginx is not proxying to correct port"
  echo "Current config: $CONFIG"
  exit 1
fi