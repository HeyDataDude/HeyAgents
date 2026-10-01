from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.enums import ReportType
from app.core.ids import report_id
from app.db.base import Base, TimestampMixin
from app.models.types import JSONColumn


class Report(Base, TimestampMixin):
    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=report_id)
    type: Mapped[str] = mapped_column(
        String, default=ReportType.DAILY.value, index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String, nullable=False)

    range_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    range_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    generated_by: Mapped[str] = mapped_column(String, default="chief_of_staff", nullable=False)

    # Structured, section-based content so the UI can render + link to evidence.
    content: Mapped[dict] = mapped_column(JSONColumn, default=dict, nullable=False)
    related_objects: Mapped[list] = mapped_column(JSONColumn, default=list, nullable=False)
