#!/bin/sh
DB_STATUS=$(docker inspect \
  --format='{{.State.Status}}' \
  environment-db-1 2>/dev/null)

if [ "$DB_STATUS" != "running" ]; then
  echo "FAIL: Container db is not running (status: $DB_STATUS)"
  exit 1
fi

echo "OK: Database container is running"

HEALTH=$(docker exec environment-backend-1 \
  curl -s http://localhost:5000/health 2>/dev/null)

if echo "$HEALTH" | grep -q '"db":"ok"'; then
  echo "OK: Backend successfully connects to database"
  exit 0
else
  echo "FAIL: Backend cannot connect to database"
  echo "Health response: $HEALTH"
  exit 1
fi