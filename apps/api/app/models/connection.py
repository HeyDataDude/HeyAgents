from __future__ import annotations

from sqlalchemy import Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.enums import ConnectionType
from app.core.ids import connection_id
from app.db.base import Base, TimestampMixin
from app.models.types import JSONColumn


class Connection(Base, TimestampMixin):
    """A cross-agent intelligence finding. Every connection has explainable provenance."""

    __tablename__ = "connections"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=connection_id)
    type: Mapped[str] = mapped_column(
        String, default=ConnectionType.RELATED_THOUGHT.value, index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, default="", nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)

    # List of {type, id, label} describing exactly which objects are linked (provenance).
    related_objects: Mapped[list] = mapped_column(JSONColumn, default=list, nullable=False)
    discovered_by: Mapped[str] = mapped_column(String, default="cross_agent", nullable=False)
    dismissed: Mapped[bool] = mapped_column(default=False, nullable=False)
