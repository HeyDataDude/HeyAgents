from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.enums import InterruptionPolicy, QuestionStatus
from app.core.ids import question_id
from app.db.base import Base, TimestampMixin


class AgentQuestion(Base, TimestampMixin):
    """An agent's request for user input/decision, routed by interruption policy."""

    __tablename__ = "agent_questions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=question_id)
    agent_id: Mapped[str] = mapped_column(ForeignKey("agents.id"), index=True, nullable=False)
    thought_id: Mapped[str | None] = mapped_column(
        ForeignKey("thoughts.id"), index=True, nullable=True
    )

    question: Mapped[str] = mapped_column(Text, nullable=False)
    context: Mapped[str] = mapped_column(Text, default="", nullable=False)
    importance: Mapped[str] = mapped_column(
        String, default=InterruptionPolicy.NEEDS_DECISION.value, nullable=False
    )

    status: Mapped[str] = mapped_column(
        String, default=QuestionStatus.OPEN.value, index=True, nullable=False
    )
    answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
