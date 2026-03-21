from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user
from app.db.db_session import get_db
from app.db.models import Environment, User
from app.schemas.environment import EnvironmentDetailResponse, EnvironmentResponse

router = APIRouter(prefix="/environments", tags=["environments"])


# получение списка всех окружений
@router.get("", response_model=list[EnvironmentResponse])
async def list_environments(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Environment))
    environments = result.scalars().all()
    return environments


# получение детальной информации об окружении вместе со списком сценариев
@router.get("/{environment_id}", response_model=EnvironmentDetailResponse)
async def get_environment(
    environment_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Environment)
        .where(Environment.id == environment_id)
        .options(selectinload(Environment.scenarios))
    )
    environment = result.scalar_one_or_none()

    if environment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Окружение не найдено",
        )

    return environment