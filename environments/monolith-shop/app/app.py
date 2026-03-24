import logging
import os
import random
import threading
import time

import psycopg2
import redis
from flask import Flask, jsonify

# настраиваем логирование в стандартном формате
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

app = Flask(__name__)


def get_db_connection():
    return psycopg2.connect(
        host=os.environ.get("DB_HOST", "db"),
        port=os.environ.get("DB_PORT", 5432),
        dbname=os.environ.get("DB_NAME", "shop"),
        user=os.environ.get("DB_USER", "shop"),
        password=os.environ.get("DB_PASSWORD", "shop"),
        connect_timeout=3,
    )


def get_redis_connection():
    return redis.Redis(
        host=os.environ.get("REDIS_HOST", "redis"),
        port=6379,
        socket_connect_timeout=3,
    )


def simulate_shop_activity():
    """
    Фоновый поток имитирует активность интернет-магазина:
    - обращения к БД (просмотры товаров, заказы)
    - обращения к Redis (кэш, сессии)
    - логирует ошибки когда сервисы недоступны
    """
    # ждём пока все сервисы запустятся
    time.sleep(10)
    logger.info("Shop activity simulation started")

    actions = [
        ("GET /products", "Fetching product catalog from DB"),
        ("GET /products/42", "Fetching product details"),
        ("POST /cart/add", "Adding item to cart"),
        ("GET /cart", "Fetching cart from cache"),
        ("POST /orders", "Creating new order"),
        ("GET /orders/history", "Fetching order history"),
    ]

    while True:
        action, description = random.choice(actions)

        # имитируем обращение к Redis (сессии, кэш)
        try:
            r = get_redis_connection()
            r.ping()

            # имитируем чтение/запись кэша
            cache_key = f"cache:{action.replace(' ', '_')}"
            r.setex(cache_key, 30, "cached_value")
            logger.info(f"{action} - cache hit - {description}")

        except Exception as e:
            logger.error(
                f"{action} - Redis unavailable: {e} - falling back to DB"
            )

        # имитируем обращение к БД
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            conn.close()
            logger.info(f"{action} - DB query OK - {description}")

        except Exception as e:
            logger.error(
                f"{action} - DB connection failed: {e}"
            )
            logger.error(
                "CRITICAL: Cannot process request - database is unavailable"
            )

        # случайная задержка между запросами 3-8 секунд
        time.sleep(random.uniform(3, 8))


@app.route("/health")
def health():
    status = {"status": "ok", "db": "ok", "redis": "ok"}

    try:
        conn = get_db_connection()
        conn.close()
    except Exception as e:
        status["db"] = f"error: {str(e)}"
        status["status"] = "degraded"
        logger.error(f"Health check - DB error: {e}")

    try:
        r = get_redis_connection()
        r.ping()
    except Exception as e:
        status["redis"] = f"error: {str(e)}"
        status["status"] = "degraded"
        logger.error(f"Health check - Redis error: {e}")

    return jsonify(status)


@app.route("/products")
def products():
    # сначала пробуем кэш
    try:
        r = get_redis_connection()
        cached = r.get("products")
        if cached:
            logger.info("GET /products - served from cache")
            return jsonify({
                "source": "cache",
                "products": ["Laptop", "Phone", "Tablet"],
            })
    except Exception as e:
        logger.warning(f"GET /products - Redis unavailable: {e}")

    # fallback на БД
    try:
        conn = get_db_connection()
        conn.close()
        logger.info("GET /products - served from DB")
        return jsonify({
            "source": "db",
            "products": ["Laptop", "Phone", "Tablet"],
        })
    except Exception as e:
        logger.error(f"GET /products - DB error: {e}")
        return jsonify({"error": "Service unavailable"}), 500


@app.route("/orders", methods=["POST"])
def create_order():
    try:
        conn = get_db_connection()
        conn.close()
        logger.info("POST /orders - order created successfully")
        return jsonify({"order_id": random.randint(1000, 9999)}), 201
    except Exception as e:
        logger.error(f"POST /orders - failed to create order: {e}")
        return jsonify({"error": "Cannot process order"}), 500


def simulate_nginx_traffic():
    """
    Имитирует входящий трафик через nginx.
    Это заставляет nginx писать логи доступа и ошибок.
    """
    time.sleep(15)
    logger.info("Starting traffic simulation through nginx")

    endpoints = ["/products", "/health", "/orders"]

    while True:
        try:
            import urllib.request
            # обращаемся через nginx (порт 80)
            endpoint = random.choice(endpoints)
            url = f"http://nginx:80{endpoint}"
            req = urllib.request.urlopen(url, timeout=3)
            logger.info(f"Traffic simulation: {req.status} {endpoint}")
        except Exception as e:
            logger.warning(f"Traffic simulation error: {e}")

        time.sleep(random.uniform(5, 10))


if __name__ == "__main__":
    time.sleep(5)
    logger.info("Starting shop backend...")

    # запускаем фоновую имитацию активности
    activity_thread = threading.Thread(
        target=simulate_shop_activity,
        daemon=True,
    )
    activity_thread.start()

    traffic_thread = threading.Thread(
        target=simulate_nginx_traffic,
        daemon=True,
    )
    traffic_thread.start()

    logger.info("Backend started successfully")
    app.run(host="0.0.0.0", port=5000, debug=False)