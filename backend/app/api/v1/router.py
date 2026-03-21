from fastapi import APIRouter

from app.api.v1 import auth, environments, sessions, containers, scenarios

router = APIRouter(prefix="/api/v1")
router.include_router(auth.router)
router.include_router(environments.router)
router.include_router(sessions.router)
router.include_router(containers.router)
router.include_router(scenarios.router)