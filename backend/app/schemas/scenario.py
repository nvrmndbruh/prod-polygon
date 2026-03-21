import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


# подсказка к сценарию
class HintResponse(BaseModel):
    id: uuid.UUID
    order_number: int
    text: str
    documentation_link: Optional[str] = None

    class Config:
        from_attributes = True


# полная информация о сценарии со списком подсказок
class ScenarioResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str
    difficulty: str
    hints: list[HintResponse] = []

    class Config:
        from_attributes = True


# результат проверки решения
class ValidationResultResponse(BaseModel):
    id: uuid.UUID
    success: bool
    message: Optional[str]
    validated_at: datetime
    used_hints: int

    class Config:
        from_attributes = True