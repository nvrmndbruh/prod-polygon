from datetime import datetime, timezone
import asyncio
import logging
import threading
from copy import deepcopy
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_active_session, get_current_user
from app.db.db_session import get_db
from app.db.models import Environment, Session, SessionStatus, User
from app.schemas.session import SessionCreate, SessionResponse
from app.services.lxc_service import lxc_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sessions", tags=["sessions"])


_startup_lock = threading.Lock()
_startup_state: dict[str, dict[str, Any]] = {}
_launching_stages = {
    "queued",
    "lxd_starting",
    "provisioning",
    "compose_starting",
    "services_booting",
    "health_checks",
}


def _set_state(
    session_id: str,
    *,
    stage: str,
    message: str,
    error: str | None = None,
) -> None:
    with _startup_lock:
        _startup_state[session_id] = {
            "stage": stage,
            "message": message,
            "error": error,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }


def _get_state(session_id: str) -> dict[str, Any] | None:
    with _startup_lock:
        state = _startup_state.get(session_id)
        return deepcopy(state) if state else None


def _clear_state(session_id: str) -> None:
    with _startup_lock:
        _startup_state.pop(session_id, None)


def _state_age_seconds(state: dict[str, Any] | None) -> float | None:
    if not state:
        return None

    updated_at = state.get("updated_at")
    if not updated_at:
        return None

    try:
        updated_dt = datetime.fromisoformat(updated_at)
    except Exception:
        return None

    return (datetime.now(timezone.utc) - updated_dt).total_seconds()


async def _start_environment_task(session_id: str, environment_path: str) -> None:
    loop = asyncio.get_running_loop()

    def progress_cb(stage: str, message: str) -> None:
        _set_state(session_id, stage=stage, message=message)

    try:
        _set_state(
            session_id,
            stage="queued",
            message="Окружение поставлено в очередь на запуск...",
        )
        await loop.run_in_executor(
            None,
            lambda: lxc_service.start_environment(
                session_id=session_id,
                environment_path=environment_path,
                progress_callback=progress_cb,
            ),
        )
    except RuntimeError as exc:
        logger.error("Failed to start environment for session %s: %s", session_id, exc)
        _set_state(
            session_id,
            stage="failed",
            message="Не удалось запустить окружение",
            error=str(exc),
        )
    except Exception as exc:
        logger.exception("Unexpected startup error for session %s", session_id)
        _set_state(
            session_id,
            stage="failed",
            message="Неожиданная ошибка запуска окружения",
            error=str(exc),
        )


@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    data: SessionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    existing_result = await db.execute(
        select(Session).where(
            Session.user_id == current_user.id,
            Session.status == SessionStatus.ACTIVE,
        )
    )
    existing_session = existing_result.scalar_one_or_none()

    if existing_session:
        existing_id = str(existing_session.id)
        existing_state = _get_state(existing_id)
        loop = asyncio.get_running_loop()
        container_exists = await loop.run_in_executor(
            None,
            lambda: lxc_service.container_exists(existing_id),
        )

        if container_exists or (
            existing_state
            and existing_state.get("stage") in _launching_stages
        ):
            return existing_session

        existing_session.status = SessionStatus.FINISHED
        existing_session.end_time = datetime.now(timezone.utc)
        await db.commit()
        _clear_state(existing_id)

    env_result = await db.execute(
        select(Environment).where(Environment.id == data.environment_id)
    )
    environment = env_result.scalar_one_or_none()

    if environment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Окружение не найдено",
        )

    session = Session(
        user_id=current_user.id,
        environment_id=environment.id,
        status=SessionStatus.ACTIVE,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)

    asyncio.create_task(
        _start_environment_task(
            session_id=str(session.id),
            environment_path=environment.path_to_config,
        )
    )

    return session


@router.get("/current", response_model=SessionResponse)
async def get_current_session(
    current_session: Session = Depends(get_active_session),
    db: AsyncSession = Depends(get_db),
):
    session_id = str(current_session.id)
    current_state = _get_state(session_id)

    if current_state and current_state.get("stage") in (_launching_stages | {"ready"}):
        return current_session

    loop = asyncio.get_running_loop()
    status_info = await loop.run_in_executor(
        None,
        lambda: lxc_service.get_session_status(session_id),
    )

    if status_info.get("exists", False):
        return current_session

    session_start_time = current_session.start_time
    if session_start_time.tzinfo is None:
        session_start_time = session_start_time.replace(tzinfo=timezone.utc)

    session_age_seconds = (datetime.now(timezone.utc) - session_start_time).total_seconds()
    if session_age_seconds < 120:
        return current_session

    current_session.status = SessionStatus.FINISHED
    current_session.end_time = datetime.now(timezone.utc)
    await db.commit()
    _clear_state(session_id)

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Активная сессия не найдена",
    )


@router.get("/{session_id}/status")
async def get_session_status(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Session).where(
            Session.id == session_id,
            Session.user_id == current_user.id,
        )
    )
    session = result.scalar_one_or_none()

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Сессия не найдена",
        )

    if session.status != SessionStatus.ACTIVE:
        return {
            "session_id": session_id,
            "is_ready": False,
            "exists": False,
            "status": session.status.value,
            "stage": "finished",
            "message": "Сессия не активна",
            "error": None,
            "running_count": 0,
            "total_count": 0,
            "containers": [],
            "connections": [],
            "connections_ok": False,
        }

    state = _get_state(str(session.id))
    loop = asyncio.get_running_loop()
    status_info = await loop.run_in_executor(
        None,
        lambda: lxc_service.get_session_status(str(session.id)),
    )

    if state and state.get("stage") == "failed" and not status_info.get("exists", False):
        failed_age = _state_age_seconds(state)
        if failed_age is not None and failed_age < 120:
            return {
                "session_id": session_id,
                "is_ready": False,
                "exists": False,
                "stage": "lxd_starting",
                "message": "Запуск LXD-контейнера...",
                "error": None,
                "running_count": 0,
                "total_count": 0,
                "containers": [],
                "connections": [],
                "connections_ok": False,
            }

        return {
            "session_id": session_id,
            "is_ready": False,
            "exists": False,
            "stage": "failed",
            "message": state.get("message") or "Не удалось запустить окружение",
            "error": state.get("error"),
            "running_count": 0,
            "total_count": 0,
            "containers": [],
            "connections": [],
            "connections_ok": False,
        }

    stage = "lxd_starting"
    message = "Запуск LXD-контейнера..."
    error = None

    if not status_info.get("exists", False):
        if state and state.get("stage") in {"queued", "lxd_starting"}:
            stage = state.get("stage", stage)
            message = state.get("message", message)
    else:
        lxd_status = status_info.get("lxd_status")
        total_count = status_info.get("total_count", 0)
        running_count = status_info.get("running_count", 0)
        connections_ok = status_info.get("connections_ok", False)

        if lxd_status != "Running":
            stage = "lxd_starting"
            message = f"Запуск LXD-контейнера ({lxd_status})..."
        elif total_count == 0:
            stage = "compose_starting"
            message = "Запуск Docker-контейнеров..."
        elif running_count < total_count:
            stage = "services_booting"
            message = f"Запуск контейнеров ({running_count}/{total_count})..."
        elif not connections_ok:
            stage = "health_checks"
            message = "Проверка связей между сервисами..."
        else:
            stage = "ready"
            message = "Окружение готово"

    if stage == "ready":
        _set_state(str(session.id), stage="ready", message="Окружение готово")

    return {
        "session_id": session_id,
        "is_ready": bool(status_info.get("is_ready", False)),
        "exists": status_info.get("exists", False),
        "containers": status_info.get("containers", []),
        "running_count": status_info.get("running_count", 0),
        "total_count": status_info.get("total_count", 0),
        "stage": stage,
        "message": message,
        "error": error,
        "connections": status_info.get("connections", []),
        "connections_ok": status_info.get("connections_ok", False),
    }


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def stop_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Session).where(
            Session.id == session_id,
            Session.user_id == current_user.id,
        )
    )
    session = result.scalar_one_or_none()

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Сессия не найдена",
        )

    if session.status != SessionStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Сессия уже завершена",
        )

    try:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None,
            lambda: lxc_service.stop_environment(session_id=str(session.id)),
        )
    except Exception:
        pass

    session.status = SessionStatus.FINISHED
    session.end_time = datetime.now(timezone.utc)
    await db.commit()
    _clear_state(str(session.id))


@router.post("/{session_id}/restart", status_code=status.HTTP_200_OK)
async def restart_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Session).where(
            Session.id == session_id,
            Session.user_id == current_user.id,
        )
    )
    session = result.scalar_one_or_none()

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Сессия не найдена",
        )

    if session.status != SessionStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Сессия не активна",
        )

    try:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None,
            lambda: lxc_service.restart_environment(str(session.id)),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )

    _set_state(
        str(session.id),
        stage="services_booting",
        message="Перезапуск контейнеров окружения...",
    )
    return {"message": "Окружение перезапущено"}