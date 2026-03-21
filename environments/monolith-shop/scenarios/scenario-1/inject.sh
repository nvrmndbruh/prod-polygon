#!/bin/sh
# сценарий 1: останавливаем контейнер с базой данных
# пользователь должен диагностировать проблему по логам
# и перезапустить контейнер db

# получаем имя проекта из переменной окружения
PROJECT=${COMPOSE_PROJECT_NAME:-prodpolygon}

echo "Simulating database failure..."
docker stop "${PROJECT}-db-1" 2>/dev/null || \
docker stop "${PROJECT}_db_1" 2>/dev/null || \
echo "Container stopped"
echo "Done. The database is now unavailable."