import uuid

from pydantic import BaseModel


# краткая информация о сценарии окружения
class ScenarioShort(BaseModel):
    id: uuid.UUID
    name: str
    description: str
    difficulty: str

    class Config:
        from_attributes = True


# краткая информация об окружении для списка
class EnvironmentResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str

    class Config:
        from_attributes = True


# полная информация об окружении
class EnvironmentDetailResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str
    scenarios: list[ScenarioShort] = []

    class Config:
        from_attributes = True