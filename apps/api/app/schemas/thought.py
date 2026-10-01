from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.core.enums import ResponseMode, ThoughtType
from app.schemas.common import ORMModel


class RoutingSuggestion(BaseModel):
    agent_id: str
    agent_slug: str
    agent_name: str
    confidence: float
    reason: str = ""


class ThoughtOut(ORMModel):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    title: str
    original_audio_uri: str | None
    audio_duration: float | None
    raw_transcript: str
    clean_transcript: str
    summary: str
    thought_type: str
    importance: int
    urgency: int
    topics: list
    entities: list
    questions: list
    ideas: list
    possible_actions: list
    routing_suggestions: list
    source: str
    capture_mode: str
    status: str
    starred: bool
    meta: dict


class CreateTextThought(BaseModel):
    text: str = Field(min_length=1)
    title: str | None = None
    source: str = "app"


class UpdateThought(BaseModel):
    title: str | None = None
    clean_transcript: str | None = None
    summary: str | None = None
    thought_type: ThoughtType | None = None
    importance: int | None = Field(default=None, ge=1, le=5)
    urgency: int | None = Field(default=None, ge=1, le=5)
    topics: list[str] | None = None
    questions: list[str] | None = None
    ideas: list[str] | None = None
    possible_actions: list[str] | None = None
    starred: bool | None = None


class DispatchRequest(BaseModel):
    recipient_agent_ids: list[str]
    response_mode: ResponseMode = ResponseMode.QUICK
    # Optional per-agent mode overrides: {agent_id: mode}
    per_agent_modes: dict[str, ResponseMode] = Field(default_factory=dict)
