import asyncio

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_active_session, get_current_user
from app.db.db_session import get_db
from app.db.models import Scenario, Session, User, ValidationResult
from app.schemas.scenario import ScenarioResponse, ValidationResultResponse
from app.services.lxc_service import lxc_service

router = APIRouter(prefix="/scenarios", tags=["scenarios"])


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
        loop = asyncio.get_event_loop()
        exit_code, output = await loop.run_in_executor(
            None,
            lambda: lxc_service.run_script(
                session_id=str(current_session.id),
                script_path=scenario.path_to_config,
            ),
        )
        return {"message": "Сценарий запущен", "output": output}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


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

    hints_result = await db.execute(
        select(ValidationResult).where(
            ValidationResult.session_id == current_session.id,
            ValidationResult.scenario_id == scenario_id,
        )
    )
    used_hints = len(hints_result.scalars().all())

    try:
        loop = asyncio.get_event_loop()
        exit_code, output = await loop.run_in_executor(
            None,
            lambda: lxc_service.run_script(
                session_id=str(current_session.id),
                script_path=scenario.path_to_validator,
            ),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )

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


@router.get(
    "/{scenario_id}/validation-history",
    response_model=list[ValidationResultResponse],
)
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