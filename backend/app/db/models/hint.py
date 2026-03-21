import uuid
from typing import Optional

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models.base import Base


# модель подсказки
class Hint(Base):
    __tablename__ = "hints"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    scenario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("scenarios.id", ondelete="CASCADE"),
        nullable=False,
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    order_number: Mapped[int] = mapped_column(Integer, nullable=False)
    documentation_link: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )

    scenario: Mapped["Scenario"] = relationship(back_populates="hints")