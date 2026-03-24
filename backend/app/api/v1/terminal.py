import asyncio
import json
import ssl

import websockets
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from sqlalchemy import select

from app.core.config import settings
from app.core.security import decode_access_token
from app.db.db_session import AsyncSessionLocal
from app.db.models import Session, SessionStatus, User
from app.services.lxc_service import lxc_service

router = APIRouter(prefix="/ws", tags=["terminal"])


def create_lxd_ssl_context() -> ssl.SSLContext:
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    ctx.load_cert_chain(
        certfile=settings.LXD_CERT,
        keyfile=settings.LXD_KEY,
    )
    return ctx


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
    cols: int = Query(default=80),
    rows: int = Query(default=24),
):
    await websocket.accept()

    user = await get_user_from_token(token)
    if user is None:
        await websocket.send_text("Ошибка: недействительный токен\r\n")
        await websocket.close()
        return

    session = await get_active_session_for_user(user.id)
    if session is None:
        await websocket.send_text("Ошибка: активная сессия не найдена\r\n")
        await websocket.close()
        return

    if not lxc_service.container_exists(str(session.id)):
        await websocket.send_text("Ошибка: контейнер не найден\r\n")
        await websocket.close()
        return

    try:
        operation_id, secret, control_secret = lxc_service.get_container_websocket(
            str(session.id),
            cols=cols,
            rows=rows,
        )
    except Exception as e:
        await websocket.send_text(f"Ошибка подключения к контейнеру: {e}\r\n")
        await websocket.close()
        return

    lxd_host = settings.LXD_URL.replace("https://", "")
    lxd_ws_url = (
        f"wss://{lxd_host}/1.0/operations/{operation_id}"
        f"/websocket?secret={secret}"
    )
    lxd_control_url = (
        f"wss://{lxd_host}/1.0/operations/{operation_id}"
        f"/websocket?secret={control_secret}"
    )

    ssl_context = create_lxd_ssl_context()

    try:
        async with websockets.connect(lxd_ws_url, ssl=ssl_context) as lxd_ws, \
                   websockets.connect(lxd_control_url, ssl=ssl_context) as lxd_control:

            async def forward_to_client():
                try:
                    async for message in lxd_ws:
                        if isinstance(message, bytes):
                            await websocket.send_text(
                                message.decode("utf-8", errors="replace")
                            )
                        else:
                            await websocket.send_text(message)
                except Exception:
                    pass

            async def forward_to_lxd():
                try:
                    while True:
                        data = await websocket.receive_text()

                        # проверяем не является ли это resize сообщением
                        try:
                            msg = json.loads(data)
                            if msg.get("type") == "resize":
                                # отправляем resize в control канал LXD
                                await lxd_control.send(json.dumps({
                                    "command": "window-resize",
                                    "args": {
                                        "width": msg.get("cols", 80),
                                        "height": msg.get("rows", 24),
                                    },
                                }))
                                continue
                        except (json.JSONDecodeError, AttributeError):
                            pass

                        # обычный ввод — отправляем в основной канал
                        await lxd_ws.send(data.encode("utf-8"))

                except WebSocketDisconnect:
                    pass
                except Exception:
                    pass

            await asyncio.gather(
                forward_to_client(),
                forward_to_lxd(),
            )

    except Exception as e:
        await websocket.send_text(f"Ошибка терминала: {e}\r\n")
    finally:
        try:
            await websocket.close()
        except Exception:
            pass