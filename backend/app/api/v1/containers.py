import asyncio

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_active_session
from app.db.models import Session
from app.services.lxc_service import lxc_service

router = APIRouter(prefix="/containers", tags=["containers"])


@router.get("/connections/status")
async def get_connections_status(
    current_session: Session = Depends(get_active_session),
):
    """
    Проверяет реальную HTTP связь между сервисами внутри LXD контейнера.
    """
    try:
        loop = asyncio.get_event_loop()
        statuses = await loop.run_in_executor(
            None,
            lambda: lxc_service.check_connections(str(current_session.id)),
        )
        return {"connections": statuses}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get("")
async def list_containers(
    current_session: Session = Depends(get_active_session),
):
    try:
        loop = asyncio.get_event_loop()
        containers = await loop.run_in_executor(
            None,
            lambda: lxc_service.get_containers(str(current_session.id)),
        )
        return {"containers": containers}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get("/{service_name}/logs")
async def get_container_logs(
    service_name: str,
    lines: int = 100,
    current_session: Session = Depends(get_active_session),
):
    try:
        loop = asyncio.get_event_loop()
        logs = await loop.run_in_executor(
            None,
            lambda: lxc_service.get_logs(
                session_id=str(current_session.id),
                service_name=service_name,
                lines=lines,
            ),
        )
        return {"service": service_name, "logs": logs}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )