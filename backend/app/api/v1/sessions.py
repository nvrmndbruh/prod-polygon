from datetime import datetime, timezone
import asyncio

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_active_session, get_current_user
from app.db.db_session import get_db
from app.db.models import Environment, Session, SessionStatus, User
from app.schemas.session import SessionCreate, SessionResponse
from app.services.lxc_service import lxc_service

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    data: SessionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(
        select(Session).where(
            Session.user_id == current_user.id,
            Session.status == SessionStatus.ACTIVE,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="У вас уже есть активная сессия",
        )

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

    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: lxc_service.start_environment(
                session_id=str(session.id),
                environment_path=environment.path_to_config,
            ),
        )
    except RuntimeError as e:
        session.status = SessionStatus.FINISHED
        session.end_time = datetime.now(timezone.utc)
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )

    return session


@router.get("/current", response_model=SessionResponse)
async def get_current_session(
    current_session: Session = Depends(get_active_session),
):
    return current_session


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
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: lxc_service.stop_environment(session_id=str(session.id)),
        )
    except Exception:
        pass

    session.status = SessionStatus.FINISHED
    session.end_time = datetime.now(timezone.utc)
    await db.commit()