from __future__ import annotations

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.enums import MemoryScope
from app.core.ids import memory_id
from app.db.base import Base, TimestampMixin
from app.models.types import Embedding, JSONColumn


class Memory(Base, TimestampMixin):
    """A single memory fact at one of three scopes: GLOBAL, AGENT, or PROJECT.

    Every memory carries provenance: which agent created it and from which thought.
    """

    __tablename__ = "memories"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=memory_id)
    scope: Mapped[str] = mapped_column(
        String, default=MemoryScope.GLOBAL.value, index=True, nullable=False
    )

    # Nullable scoping targets depending on `scope`.
    agent_id: Mapped[str | None] = mapped_column(ForeignKey("agents.id"), index=True, nullable=True)
    project_id: Mapped[str | None] = mapped_column(
        ForeignKey("projects.id"), index=True, nullable=True
    )

    # A category grouping within a scope (e.g. "Projects", "Goals", "People").
    category: Mapped[str] = mapped_column(String, default="General", index=True, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Provenance.
    created_by_agent_id: Mapped[str | None] = mapped_column(
        ForeignKey("agents.id"), nullable=True
    )
    originating_thought_id: Mapped[str | None] = mapped_column(
        ForeignKey("thoughts.id"), index=True, nullable=True
    )
    provenance: Mapped[dict] = mapped_column(JSONColumn, default=dict, nullable=False)

    embedding = mapped_column(Embedding(1536), nullable=True)
