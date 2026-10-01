from __future__ import annotations

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.ids import activity_id
from app.db.base import Base, TimestampMixin
from app.models.types import JSONColumn


class Activity(Base, TimestampMixin):
    """A human-readable, link-rich event in the system's activity feed (§34)."""

    __tablename__ = "activities"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=activity_id)
    kind: Mapped[str] = mapped_column(String, index=True, nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    actor: Mapped[str] = mapped_column(String, default="system", nullable=False)  # agent slug/system
    # List of {type, id, label} links so the UI can navigate to related objects.
    links: Mapped[list] = mapped_column(JSONColumn, default=list, nullable=False)
    level: Mapped[str] = mapped_column(String, default="info", nullable=False)
