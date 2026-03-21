#!/bin/sh
# проверяем, что контейнер db снова запущен
# и бэкенд успешно подключается к БД

PROJECT=${COMPOSE_PROJECT_NAME:-prodpolygon}

# проверяем статус контейнера db
DB_STATUS=$(docker inspect \
  --format='{{.State.Status}}' \
  "${PROJECT}-db-1" 2>/dev/null || \
  docker inspect \
  --format='{{.State.Status}}' \
  "${PROJECT}_db_1" 2>/dev/null)

if [ "$DB_STATUS" != "running" ]; then
  echo "FAIL: Container db is not running (status: $DB_STATUS)"
  exit 1
fi

echo "OK: Database container is running"

# проверяем, что health-эндпоинт бэкенда сообщает об успехе
HEALTH=$(docker exec "${PROJECT}-backend-1" \
  curl -s http://localhost:5000/health 2>/dev/null || \
  docker exec "${PROJECT}_backend_1" \
  curl -s http://localhost:5000/health 2>/dev/null)

if echo "$HEALTH" | grep -q '"db": "ok"'; then
  echo "OK: Backend successfully connects to database"
  exit 0
else
  echo "FAIL: Backend cannot connect to database"
  echo "Health response: $HEALTH"
  exit 1
fi