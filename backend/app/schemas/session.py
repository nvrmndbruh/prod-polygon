import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


# данные для создания новой сессии
class SessionCreate(BaseModel):
    environment_id: uuid.UUID


# данные активной сессии
class SessionResponse(BaseModel):
    id: uuid.UUID
    environment_id: Optional[uuid.UUID]
    status: str
    start_time: datetime

    class Config:
        from_attributes = True