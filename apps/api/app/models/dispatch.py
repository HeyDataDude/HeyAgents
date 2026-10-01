from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.enums import AgentDispatchStatus, DispatchStatus, ResponseMode
from app.core.ids import agent_dispatch_id, dispatch_id
from app.db.base import Base, TimestampMixin
from app.models.types import JSONColumn


class Dispatch(Base, TimestampMixin):
    """A routing decision for one thought: which agents, which default mode."""

    __tablename__ = "dispatches"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=dispatch_id)
    thought_id: Mapped[str] = mapped_column(
        ForeignKey("thoughts.id"), index=True, nullable=False
    )
    recipient_agent_ids: Mapped[list] = mapped_column(JSONColumn, default=list, nullable=False)
    default_response_mode: Mapped[str] = mapped_column(
        String, default=ResponseMode.QUICK.value, nullable=False
    )
    status: Mapped[str] = mapped_column(
        String, default=DispatchStatus.PENDING.value, index=True, nullable=False
    )


class AgentDispatch(Base, TimestampMixin):
    """One row/job per recipient agent. This is the unit the worker executes."""

    __tablename__ = "agent_dispatches"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=agent_dispatch_id)
    dispatch_id: Mapped[str] = mapped_column(
        ForeignKey("dispatches.id"), index=True, nullable=False
    )
    thought_id: Mapped[str] = mapped_column(
        ForeignKey("thoughts.id"), index=True, nullable=False
    )
    agent_id: Mapped[str] = mapped_column(ForeignKey("agents.id"), index=True, nullable=False)

    response_mode: Mapped[str] = mapped_column(
        String, default=ResponseMode.QUICK.value, nullable=False
    )
    status: Mapped[str] = mapped_column(
        String, default=AgentDispatchStatus.QUEUED.value, index=True, nullable=False
    )

    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    response_summary: Mapped[str] = mapped_column(Text, default="", nullable=False)
    # Full validated agent output contract (message + structured actions).
    output: Mapped[dict] = mapped_column(JSONColumn, default=dict, nullable=False)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    read: Mapped[bool] = mapped_column(default=False, nullable=False)
