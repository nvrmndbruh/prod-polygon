import asyncio
import threading

import docker
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from sqlalchemy import select

from app.core.security import decode_access_token
from app.db.db_session import AsyncSessionLocal
from app.db.models import Session, SessionStatus, User
from app.services.docker_service import docker_service

router = APIRouter(prefix="/ws", tags=["terminal"])


async def get_user_from_token(token: str):
    payload = decode_access_token(token)
    if payload is None:
        return None
    user_id = payload.get("sub")
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()


async def get_active_session_for_user(user_id):
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Session).where(
                Session.user_id == user_id,
                Session.status == SessionStatus.ACTIVE,
            )
        )
        return result.scalar_one_or_none()


@router.websocket("/terminal")
async def terminal_websocket(
    websocket: WebSocket,
    token: str = Query(...),
):
    await websocket.accept()

    user = await get_user_from_token(token)
    if user is None:
        await websocket.send_text("Ошибка: недействительный токен\r\n")
        await websocket.close()
        return

    session = await get_active_session_for_user(user.id)
    if session is None:
        await websocket.send_text(
            "Ошибка: активная сессия не найдена\r\n"
        )
        await websocket.close()
        return

    project_name = docker_service._get_project_name(str(session.id))
    client = docker.from_env()

    containers = client.containers.list(
        filters={
            "label": [
                f"com.docker.compose.project={project_name}",
                "com.docker.compose.service=workspace",
            ]
        }
    )

    if not containers:
        await websocket.send_text(
            "Ошибка: workspace-контейнер не найден\r\n"
        )
        await websocket.close()
        return

    container = containers[0]

    exec_id = client.api.exec_create(
        container.id,
        cmd=["/bin/bash", "--login"],
        stdin=True,
        stdout=True,
        stderr=True,
        tty=True,
        user="student",
        environment=[
            f"COMPOSE_PROJECT_NAME={project_name}",
            "TERM=xterm-256color",
            "LANG=en_US.UTF-8",
            "LC_ALL=en_US.UTF-8",
        ],
    )

    sock = client.api.exec_start(
        exec_id["Id"],
        detach=False,
        tty=True,
        socket=True,
    )

    raw_sock = sock._sock
    # Устанавливаем небольшой таймаут чтобы recv не блокировал вечно
    raw_sock.settimeout(0.1)

    loop = asyncio.get_event_loop()
    stop_event = threading.Event()

    def read_from_container():
        """
        Читает вывод из контейнера в отдельном потоке
        и отправляет клиенту через WebSocket.
        Вынесено в поток чтобы не блокировать asyncio event loop.
        """
        while not stop_event.is_set():
            try:
                data = raw_sock.recv(4096)
                if data:
                    asyncio.run_coroutine_threadsafe(
                        websocket.send_text(
                            data.decode("utf-8", errors="replace")
                        ),
                        loop,
                    )
            except TimeoutError:
                # Таймаут — нормально, продолжаем ждать
                continue
            except OSError:
                break

    # Запускаем поток чтения
    reader_thread = threading.Thread(target=read_from_container, daemon=True)
    reader_thread.start()

    try:
        # Основной цикл — читаем команды от клиента и пишем в контейнер
        while True:
            data = await websocket.receive_text()
            raw_sock.send(data.encode("utf-8"))
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        stop_event.set()
        try:
            raw_sock.close()
        except Exception:
            pass
        reader_thread.join(timeout=2)