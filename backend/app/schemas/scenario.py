import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


# ответ при запросе подсказки
class HintResponse(BaseModel):
    id: uuid.UUID
    order_number: int
    text: str
    documentation_link: Optional[str] = None

    class Config:
        from_attributes = True


# ответ при запросе сценария
class ScenarioResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str
    difficulty: str
    hints: list[HintResponse] = []

    class Config:
        from_attributes = True


# ответ при запросе результата валидации
class ValidationResultResponse(BaseModel):
    id: uuid.UUID
    success: bool
    message: Optional[str]
    validated_at: datetime
    used_hints: int

    class Config:
        from_attributes = True