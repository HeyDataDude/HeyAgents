from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.enums import ResearchStatus
from app.core.ids import research_id
from app.db.base import Base, TimestampMixin
from app.models.types import JSONColumn


class ResearchJob(Base, TimestampMixin):
    __tablename__ = "research_jobs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=research_id)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    agent_id: Mapped[str | None] = mapped_column(ForeignKey("agents.id"), index=True, nullable=True)
    originating_thought_id: Mapped[str | None] = mapped_column(
        ForeignKey("thoughts.id"), index=True, nullable=True
    )

    status: Mapped[str] = mapped_column(
        String, default=ResearchStatus.QUEUED.value, index=True, nullable=False
    )
    progress: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # 0..100

    sources: Mapped[list] = mapped_column(JSONColumn, default=list, nullable=False)
    findings: Mapped[str] = mapped_column(Text, default="", nullable=False)
    artifact_uri: Mapped[str | None] = mapped_column(String, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
