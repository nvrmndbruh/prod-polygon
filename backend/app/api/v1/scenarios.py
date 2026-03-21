from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_active_session, get_current_user
from app.db.db_session import get_db
from app.db.models import Scenario, Session, User, ValidationResult
from app.schemas.scenario import ScenarioResponse, ValidationResultResponse
from app.services.docker_service import docker_service

router = APIRouter(prefix="/scenarios", tags=["scenarios"])


# получение информации о сценарии и его подсказках
@router.get("/{scenario_id}", response_model=ScenarioResponse)
async def get_scenario(
    scenario_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Scenario)
        .where(Scenario.id == scenario_id)
        .options(selectinload(Scenario.hints))
    )
    scenario = result.scalar_one_or_none()

    if scenario is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Сценарий не найден",
        )

    return scenario


# запуск сценария
@router.post("/{scenario_id}/start", status_code=status.HTTP_200_OK)
async def start_scenario(
    scenario_id: str,
    current_session: Session = Depends(get_active_session),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Scenario).where(Scenario.id == scenario_id)
    )
    scenario = result.scalar_one_or_none()

    if scenario is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Сценарий не найден",
        )

    try:
        # запускаем inject.sh — скрипт который ломает окружение
        # скрипт выполняется на хосте через docker_service,
        # передаём имя проекта как переменную окружения
        exit_code, output = docker_service.run_host_script(
            session_id=str(current_session.id),
            script_path=scenario.path_to_config,
        )
        return {"message": "Сценарий запущен", "output": output}
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


# проверка решения пользователя
@router.post("/{scenario_id}/validate", response_model=ValidationResultResponse)
async def validate_scenario(
    scenario_id: str,
    current_session: Session = Depends(get_active_session),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Scenario).where(Scenario.id == scenario_id)
    )
    scenario = result.scalar_one_or_none()

    if scenario is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Сценарий не найден",
        )

    # считаем сколько подсказок использовал пользователь
    hints_result = await db.execute(
        select(ValidationResult).where(
            ValidationResult.session_id == current_session.id,
            ValidationResult.scenario_id == scenario_id,
        )
    )
    previous_attempts = hints_result.scalars().all()
    used_hints = len(previous_attempts)

    try:
        exit_code, output = docker_service.run_host_script(
            session_id=str(current_session.id),
            script_path=scenario.path_to_validator,
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )

    # exit_code 0 означает успех
    success = exit_code == 0

    validation_result = ValidationResult(
        session_id=current_session.id,
        scenario_id=scenario.id,
        success=success,
        message=output,
        used_hints=used_hints,
    )
    db.add(validation_result)
    await db.commit()
    await db.refresh(validation_result)

    return validation_result


# история попыток проверки решения
@router.get("/{scenario_id}/validation-history",
            response_model=list[ValidationResultResponse])
async def get_validation_history(
    scenario_id: str,
    current_session: Session = Depends(get_active_session),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ValidationResult).where(
            ValidationResult.session_id == current_session.id,
            ValidationResult.scenario_id == scenario_id,
        )
    )
    return result.scalars().all()