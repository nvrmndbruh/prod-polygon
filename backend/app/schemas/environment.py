import uuid

from pydantic import BaseModel, Field


# краткая информация о сценарии
class ScenarioShort(BaseModel):
    id: uuid.UUID
    name: str
    description: str
    difficulty: str

    class Config:
        from_attributes = True


# ответ при запросе информации об окружении
class EnvironmentResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str
    is_available: bool = True

    class Config:
        from_attributes = True


# ответ при запросе информации об окружении с подробностями
class EnvironmentDetailResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str
    scenarios: list[ScenarioShort] = Field(default_factory=list)
    is_available: bool = True

    class Config:
        from_attributes = True