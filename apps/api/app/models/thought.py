from __future__ import annotations

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.enums import CaptureMode, ThoughtStatus, ThoughtType
from app.core.ids import thought_id
from app.db.base import Base, TimestampMixin
from app.models.types import Embedding, JSONColumn


class Thought(Base, TimestampMixin):
    """The fundamental input unit. The original audio and raw transcript are never overwritten."""

    __tablename__ = "thoughts"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=thought_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)

    title: Mapped[str] = mapped_column(String, default="Untitled thought", nullable=False)

    # Capture / provenance — preserved permanently.
    original_audio_uri: Mapped[str | None] = mapped_column(String, nullable=True)
    audio_duration: Mapped[float | None] = mapped_column(Float, nullable=True)

    raw_transcript: Mapped[str] = mapped_column(Text, default="", nullable=False)
    clean_transcript: Mapped[str] = mapped_column(Text, default="", nullable=False)
    summary: Mapped[str] = mapped_column(Text, default="", nullable=False)

    thought_type: Mapped[str] = mapped_column(
        String, default=ThoughtType.NOTE.value, nullable=False
    )
    importance: Mapped[int] = mapped_column(Integer, default=3, nullable=False)  # 1..5
    urgency: Mapped[int] = mapped_column(Integer, default=2, nullable=False)  # 1..5

    # Structured extraction — explicit, never a loose blob of chat JSON.
    topics: Mapped[list] = mapped_column(JSONColumn, default=list, nullable=False)
    entities: Mapped[list] = mapped_column(JSONColumn, default=list, nullable=False)
    questions: Mapped[list] = mapped_column(JSONColumn, default=list, nullable=False)
    ideas: Mapped[list] = mapped_column(JSONColumn, default=list, nullable=False)
    possible_actions: Mapped[list] = mapped_column(JSONColumn, default=list, nullable=False)
    routing_suggestions: Mapped[list] = mapped_column(JSONColumn, default=list, nullable=False)

    source: Mapped[str] = mapped_column(String, default="app", nullable=False)
    capture_mode: Mapped[str] = mapped_column(
        String, default=CaptureMode.VOICE.value, nullable=False
    )
    status: Mapped[str] = mapped_column(
        String, default=ThoughtStatus.CAPTURED.value, index=True, nullable=False
    )
    starred: Mapped[bool] = mapped_column(default=False, nullable=False)

    embedding = mapped_column(Embedding(1536), nullable=True)

    meta: Mapped[dict] = mapped_column(JSONColumn, default=dict, nullable=False)
