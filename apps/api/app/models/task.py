from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.enums import Priority, TaskStatus
from app.core.ids import task_id
from app.db.base import Base, TimestampMixin


class Task(Base, TimestampMixin):
    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=task_id)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)

    created_by_agent_id: Mapped[str | None] = mapped_column(
        ForeignKey("agents.id"), index=True, nullable=True
    )
    originating_thought_id: Mapped[str | None] = mapped_column(
        ForeignKey("thoughts.id"), index=True, nullable=True
    )
    project_id: Mapped[str | None] = mapped_column(
        ForeignKey("projects.id"), index=True, nullable=True
    )

    status: Mapped[str] = mapped_column(
        String, default=TaskStatus.TODO.value, index=True, nullable=False
    )
    priority: Mapped[str] = mapped_column(
        String, default=Priority.MEDIUM.value, nullable=False
    )
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Autonomy gate: tasks that touch the external world need explicit approval.
    requires_user_approval: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    approved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Why does this task exist? (human-readable rationale from the agent)
    rationale: Mapped[str] = mapped_column(Text, default="", nullable=False)
