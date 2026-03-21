import os
import time

import redis
import psycopg2
from flask import Flask, jsonify

app = Flask(__name__)

# получение соединения с базой данных
def get_db_connection():
    return psycopg2.connect(
        host=os.environ.get("DB_HOST", "db"),
        port=os.environ.get("DB_PORT", 5432),
        dbname=os.environ.get("DB_NAME", "shop"),
        user=os.environ.get("DB_USER", "shop"),
        password=os.environ.get("DB_PASSWORD", "shop"),
        connect_timeout=3,
    )

# получение соединения с Redis
def get_redis_connection():
    return redis.Redis(
        host=os.environ.get("REDIS_HOST", "redis"),
        port=6379,
        socket_connect_timeout=3,
    )

# эндпоинт для проверки здоровья приложения и его зависимостей
@app.route("/health")
def health():
    status = {"status": "ok", "services": {}}

    # проверяем БД
    try:
        conn = get_db_connection()
        conn.close()
        status["services"]["db"] = "ok"
    except Exception as e:
        status["services"]["db"] = f"error: {str(e)}"
        status["status"] = "degraded"

    # проверяем Redis
    try:
        r = get_redis_connection()
        r.ping()
        status["services"]["redis"] = "ok"
    except Exception as e:
        status["services"]["redis"] = f"error: {str(e)}"
        status["status"] = "degraded"

    return jsonify(status)


# эндпоинт для получения списка продуктов
@app.route("/products")
def products():
    try:
        r = get_redis_connection()
        cached = r.get("products")
        if cached:
            return jsonify({"source": "cache", "products": ["product1", "product2"]})
    except Exception:
        pass

    try:
        conn = get_db_connection()
        conn.close()
        return jsonify({"source": "db", "products": ["product1", "product2"]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    # небольшая пауза чтобы БД успела запуститься
    time.sleep(5)
    app.run(host="0.0.0.0", port=5000, debug=True)