import asyncio
import uuid

from sqlalchemy import select

from app.db.db_session import AsyncSessionLocal
from app.db.models import Environment, Scenario, Hint, Difficulty


# скрипт для заполнения базы начальными данными
async def seed():
    async with AsyncSessionLocal() as db:
        # проверяем на заполненность
        result = await db.execute(select(Environment))
        if result.scalar_one_or_none():
            print("Database already seeded, skipping.")
            return

        # создаём окружение магазина
        shop_environment = Environment(
            id=uuid.uuid4(),
            name="Интернет-магазин",
            description=(
                "Монолитное приложение интернет-магазина. "
                "Включает Nginx в качестве реверс-прокси, "
                "Flask-бэкенд, PostgreSQL и Redis. "
                "Архитектура типична для небольших e-commerce проектов."
            ),
            path_to_config="monolith-shop",
        )
        db.add(shop_environment)
        await db.flush()

        # создаём окружение банка
        bank_environment = Environment(
            id=uuid.uuid4(),
            name="Онлайн-банк",
            description=(
                "Микросервисное приложение онлайн-банка. "
                "Включает API Gateway, сервис пользователей, платёжный сервис, "
                "сервис уведомлений, PostgreSQL, Redis. "
                "Архитектура типична для современных финансовых приложений."
            ),
            path_to_config="microservices-bank",
        )
        db.add(bank_environment)
        await db.flush()

        # окружение системы обработки данных
        event_environment = Environment(
            id=uuid.uuid4(),
            name="Система обработки данных",
            description=(
                "Событийно-ориентированная архитектура. "
                "Включает Producer, RabbitMQ, Consumer, PostgreSQL. "
                "Асинхронное взаимодействие через брокер сообщений и "
                "типичные проблемы очередей."
            ),
            path_to_config="microservices-data-processing",
        )
        db.add(event_environment)
        await db.flush()

        # сценарий 1
        scenario1 = Scenario(
            id=uuid.uuid4(),
            environment_id=shop_environment.id,
            name="База данных недоступна",
            description=(
                "PostgreSQL неожиданно перестал отвечать. "
                "Бэкенд не может выполнять запросы к БД, "
                "эндпоинт /products возвращает ошибку 500. "
                "Найдите причину и восстановите работу системы."
            ),
            difficulty=Difficulty.EASY,
            path_to_config="monolith-shop/scenarios/scenario-1/inject.sh",
            path_to_validator="monolith-shop/scenarios/scenario-1/validate.sh",
        )
        db.add(scenario1)
        await db.flush()

        # подсказки к сценарию 1
        hints1 = [
            Hint(
                scenario_id=scenario1.id,
                order_number=1,
                text="Проверьте статус всех контейнеров окружения командой docker ps -a",
                documentation_link=None,
            ),
            Hint(
                scenario_id=scenario1.id,
                order_number=2,
                text="Посмотрите логи бэкенда — там должна быть ошибка подключения к БД",
                documentation_link=None,
            ),
            Hint(
                scenario_id=scenario1.id,
                order_number=3,
                text="Контейнер с базой данных остановлен. Запустите его командой docker start",
                documentation_link="https://docs.docker.com/engine/reference/commandline/start/",
            ),
        ]
        db.add_all(hints1)

        # сценарий 2
        scenario2 = Scenario(
            id=uuid.uuid4(),
            environment_id=shop_environment.id,
            name="Неверная конфигурация Nginx",
            description=(
                "Все запросы к сайту возвращают ошибку 502 Bad Gateway. "
                "Nginx запущен, бэкенд тоже работает, "
                "но что-то настроено неправильно. "
                "Найдите и исправьте проблему в конфигурации."
            ),
            difficulty=Difficulty.EASY,
            path_to_config="monolith-shop/scenarios/scenario-2/inject.sh",
            path_to_validator="monolith-shop/scenarios/scenario-2/validate.sh",
        )
        db.add(scenario2)
        await db.flush()

        # подсказки к сценарию 2
        hints2 = [
            Hint(
                scenario_id=scenario2.id,
                order_number=1,
                text="Проверьте логи Nginx — там будет указано, к какому адресу он пытается подключиться",
                documentation_link=None,
            ),
            Hint(
                scenario_id=scenario2.id,
                order_number=2,
                text="Посмотрите конфигурацию Nginx: docker exec <container> cat /etc/nginx/conf.d/default.conf",
                documentation_link=None,
            ),
            Hint(
                scenario_id=scenario2.id,
                order_number=3,
                text="В директиве proxy_pass указан неверный порт. Flask-приложение слушает порт 5000",
                documentation_link="https://nginx.org/en/docs/http/ngx_http_proxy_module.html#proxy_pass",
            ),
        ]
        db.add_all(hints2)

        await db.commit()
        print("Database seeded successfully.")


if __name__ == "__main__":
    asyncio.run(seed())