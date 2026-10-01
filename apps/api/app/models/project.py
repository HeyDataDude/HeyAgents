from __future__ import annotations

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.enums import ProjectStatus
from app.core.ids import project_id
from app.db.base import Base, TimestampMixin
from app.models.types import JSONColumn


class Project(Base, TimestampMixin):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=project_id)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    status: Mapped[str] = mapped_column(
        String, default=ProjectStatus.ACTIVE.value, index=True, nullable=False
    )
    goals: Mapped[list] = mapped_column(JSONColumn, default=list, nullable=False)

    related_agent_ids: Mapped[list] = mapped_column(JSONColumn, default=list, nullable=False)
    related_thought_ids: Mapped[list] = mapped_column(JSONColumn, default=list, nullable=False)
    related_task_ids: Mapped[list] = mapped_column(JSONColumn, default=list, nullable=False)
