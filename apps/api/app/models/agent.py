from __future__ import annotations

from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.enums import AutonomyLevel, InterruptionPolicy
from app.core.ids import agent_id
from app.db.base import Base, TimestampMixin


class Agent(Base, TimestampMixin):
    """A persistent specialist. Mirrors a Letta agent via `letta_agent_id` when live."""

    __tablename__ = "agents"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=agent_id)
    name: Mapped[str] = mapped_column(String, nullable=False)
    slug: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    icon: Mapped[str] = mapped_column(String, default="sparkles", nullable=False)
    accent: Mapped[str] = mapped_column(String, default="slate", nullable=False)
    system_role: Mapped[str] = mapped_column(Text, default="", nullable=False)

    provider: Mapped[str] = mapped_column(String, default="mock", nullable=False)
    model: Mapped[str] = mapped_column(String, default="gpt-4o-mini", nullable=False)
    letta_agent_id: Mapped[str | None] = mapped_column(String, nullable=True)

    autonomy_level: Mapped[int] = mapped_column(
        Integer, default=AutonomyLevel.RECOMMEND.value, nullable=False
    )
    interruption_policy: Mapped[str] = mapped_column(
        String, default=InterruptionPolicy.NORMAL.value, nullable=False
    )

    # Chief of Staff is a supervisory agent, not a domain specialist.
    is_supervisor: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Routing hint keywords used by the heuristic router / mock providers.
    routing_keywords: Mapped[str] = mapped_column(Text, default="", nullable=False)
