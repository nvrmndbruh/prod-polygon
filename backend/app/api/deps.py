from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.db.db_session import get_db
from app.db.models import User, WorkSession, SessionStatus

bearer_scheme = HTTPBearer()


# зависимость дл€ получени€ текущего пользовател€ по JWT-токену
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    token = credentials.credentials
    payload = decode_access_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Ќедействительный или истЄкший токен",
        )

    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="ѕользователь не найден",
        )

    return user


# зависимость дл€ получени€ активной сессии текущего пользовател€
async def get_active_session(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WorkSession:
    result = await db.execute(
        select(WorkSession).where(
            WorkSession.user_id == current_user.id,
            WorkSession.status == SessionStatus.ACTIVE,
        )
    )
    session = result.scalar_one_or_none()

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="јктивна€ сесси€ не найдена. —начала запустите окружение",
        )

    return session