import asyncio
import struct
import fcntl
import termios
import os
import pty
import select as io_select

import docker
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from sqlalchemy import select

from app.core.security import decode_access_token
from app.db.db_session import AsyncSessionLocal
from app.db.models import Session, SessionStatus, User
from app.services.docker_service import docker_service

router = APIRouter(prefix="/ws", tags=["terminal"])


# получение пользователя из JWT-токена
async def get_user_from_token(token: str):
    """
    Проверяет JWT-токен и возвращает пользователя.
    Используется вместо обычной зависимости get_current_user,
    потому что WebSocket не поддерживает HTTP-заголовки так же
    как обычные запросы — токен передаётся через query-параметр.
    """
    payload = decode_access_token(token)
    if payload is None:
        return None

    user_id = payload.get("sub")
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()


# получение активной сессии пользователя
async def get_active_session_for_user(user_id):
    """
    Получает активную сессию пользователя для WebSocket-подключения.
    """
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Session).where(
                Session.user_id == user_id,
                Session.status == SessionStatus.ACTIVE,
            )
        )
        return result.scalar_one_or_none()


# WebSocket-терминал для работы с контейнером окружения
@router.websocket("/terminal")
async def terminal_websocket(
    websocket: WebSocket,
    token: str = Query(..., description="JWT токен авторизации"),
):
    """
    WebSocket-терминал для работы с контейнером окружения.

    Протокол обмена сообщениями:
    - Клиент → Сервер: строка с командой (обычный текст)
    - Клиент → Сервер: JSON {"type": "resize", "rows": N, "cols": N}
    - Сервер → Клиент: вывод команды (обычный текст)
    - Сервер → Клиент: JSON {"type": "error", "message": "..."}

    Подключение: ws://localhost:8000/api/v1/ws/terminal?token=<jwt>
    """
    await websocket.accept()

    # проверяем токен
    user = await get_user_from_token(token)
    if user is None:
        await websocket.send_text(
            "Ошибка: недействительный токен авторизации\r\n"
        )
        await websocket.close()
        return

    # получаем активную сессию
    session = await get_active_session_for_user(user.id)
    if session is None:
        await websocket.send_text(
            "Ошибка: активная сессия не найдена. Запустите окружение.\r\n"
        )
        await websocket.close()
        return

    # получаем контейнер бэкенда из окружения пользователя
    project_name = docker_service._get_project_name(str(session.id))
    client = docker.from_env()

    containers = client.containers.list(
        filters={
            "label": [
                f"com.docker.compose.project={project_name}",
                "com.docker.compose.service=backend",
            ]
        }
    )

    if not containers:
        await websocket.send_text(
            "Ошибка: контейнер окружения не найден.\r\n"
        )
        await websocket.close()
        return

    container = containers[0]

    # создаём PTY (псевдотерминал) и запускаем shell в контейнере
    # PTY позволяет запустить интерактивный shell с полной поддержкой
    # управляющих символов, цветов и команд типа top, vim и т.д.
    exec_id = client.api.exec_create(
        container.id,
        cmd="/bin/sh",
        stdin=True,
        stdout=True,
        stderr=True,
        tty=True,
        environment=[f"COMPOSE_PROJECT_NAME={project_name}"],
    )

    sock = client.api.exec_start(
        exec_id["Id"],
        detach=False,
        tty=True,
        socket=True,
    )

    # получаем сырой сокет для прямого взаимодействия
    raw_sock = sock._sock
    raw_sock.setblocking(False)

    await websocket.send_text(
        "Подключение к окружению установлено. "
        "Введите команду:\r\n"
    )

    try:
        while True:
            # ждём данных одновременно от клиента и от контейнера
            # asyncio позволяет делать это без блокировки
            receive_task = asyncio.create_task(
                websocket.receive_text()
            )

            # небольшая пауза чтобы проверить вывод контейнера
            done, pending = await asyncio.wait(
                [receive_task],
                timeout=0.05,
            )

            # если клиент прислал команду — отправляем в контейнер
            if receive_task in done:
                try:
                    data = receive_task.result()
                    raw_sock.send(data.encode("utf-8"))
                except WebSocketDisconnect:
                    break
                except Exception:
                    break
            else:
                # отменяем задачу если данных от клиента нет
                receive_task.cancel()
                try:
                    await receive_task
                except asyncio.CancelledError:
                    pass

            # читаем вывод из контейнера и отправляем клиенту
            try:
                output = raw_sock.recv(4096)
                if output:
                    await websocket.send_text(
                        output.decode("utf-8", errors="replace")
                    )
            except BlockingIOError:
                # данных пока нет — это нормально
                pass
            except Exception:
                break

    except WebSocketDisconnect:
        pass
    finally:
        try:
            raw_sock.close()
        except Exception:
            pass