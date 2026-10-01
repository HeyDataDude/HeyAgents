from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.enums import JobStatus
from app.core.ids import job_id
from app.db.base import Base, TimestampMixin
from app.models.types import JSONColumn


class Job(Base, TimestampMixin):
    """Durable background job. Survives restarts: state lives in Postgres, not just Redis."""

    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=job_id)
    kind: Mapped[str] = mapped_column(String, index=True, nullable=False)
    status: Mapped[str] = mapped_column(
        String, default=JobStatus.QUEUED.value, index=True, nullable=False
    )
    progress: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    payload: Mapped[dict] = mapped_column(JSONColumn, default=dict, nullable=False)
    result: Mapped[dict] = mapped_column(JSONColumn, default=dict, nullable=False)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
