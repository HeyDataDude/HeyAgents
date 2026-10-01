from __future__ import annotations

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.enums import MessageRole
from app.core.ids import conversation_id, message_id
from app.db.base import Base, TimestampMixin
from app.models.types import JSONColumn


class Conversation(Base, TimestampMixin):
    """A chat or voice session with one agent (or the Council moderator)."""

    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=conversation_id)
    title: Mapped[str] = mapped_column(String, default="Conversation", nullable=False)
    # Single-agent chat uses agent_id; Council calls use participant_agent_ids + is_council.
    agent_id: Mapped[str | None] = mapped_column(ForeignKey("agents.id"), index=True, nullable=True)
    is_council: Mapped[bool] = mapped_column(default=False, nullable=False)
    participant_agent_ids: Mapped[list] = mapped_column(JSONColumn, default=list, nullable=False)
    mode: Mapped[str] = mapped_column(String, default="text", nullable=False)  # text|voice
    thought_id: Mapped[str | None] = mapped_column(
        ForeignKey("thoughts.id"), index=True, nullable=True
    )


class Message(Base, TimestampMixin):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=message_id)
    conversation_id: Mapped[str] = mapped_column(
        ForeignKey("conversations.id"), index=True, nullable=False
    )
    role: Mapped[str] = mapped_column(String, default=MessageRole.USER.value, nullable=False)
    # For agent messages, which agent spoke.
    agent_id: Mapped[str | None] = mapped_column(ForeignKey("agents.id"), nullable=True)
    content: Mapped[str] = mapped_column(Text, default="", nullable=False)
    meta: Mapped[dict] = mapped_column(JSONColumn, default=dict, nullable=False)
