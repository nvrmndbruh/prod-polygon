import uuid
from enum import Enum as PyEnum

from sqlalchemy import Enum, String, Text
from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models.base import Base


# сложность сценария
class Difficulty(str, PyEnum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


# модель сценария
class Scenario(Base):
    __tablename__ = "scenarios"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    environment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("environments.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(32), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    difficulty: Mapped[Difficulty] = mapped_column(
        Enum(Difficulty), nullable=False
    )
    path_to_config: Mapped[str] = mapped_column(
        String(128), unique=True, nullable=False
    )
    path_to_validator: Mapped[str] = mapped_column(
        String(128), unique=True, nullable=False
    )

    environment: Mapped["Environment"] = relationship(back_populates="scenarios")
    hints: Mapped[list["Hint"]] = relationship(
        back_populates="scenario",
        cascade="all, delete-orphan",
        order_by="Hint.order_number",
    )
    validation_results: Mapped[list["ValidationResult"]] = relationship(
        back_populates="scenario"
    )