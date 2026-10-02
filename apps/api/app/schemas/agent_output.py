"""The Agent Output Contract (spec §11).

Every agent execution returns a validated structured object — never just free text. Potentially
destructive/external actions are gated by autonomy level downstream, not executed blindly.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.core.enums import ConnectionType, InterruptionPolicy, MemoryScope, Priority


class MemoryUpdate(BaseModel):
    scope: MemoryScope = MemoryScope.AGENT
    category: str = "General"
    content: str
    project_id: str | None = None


class TaskProposal(BaseModel):
    title: str
    description: str = ""
    priority: Priority = Priority.MEDIUM
    due_at: datetime | None = None
    requires_user_approval: bool = False
    rationale: str = ""
    project_id: str | None = None


class ResearchJobProposal(BaseModel):
    question: str
    rationale: str = ""


class ProjectUpdate(BaseModel):
    project_id: str | None = None
    name: str | None = None  # when creating a new project
    note: str = ""
    add_goal: str | None = None


class QuestionForUser(BaseModel):
    question: str
    context: str = ""
    importance: InterruptionPolicy = InterruptionPolicy.NEEDS_DECISION


class ConnectionProposal(BaseModel):
    type: ConnectionType = ConnectionType.RELATED_THOUGHT
    title: str
    explanation: str
    confidence: float = 0.5
    related_object_ids: list[str] = Field(default_factory=list)


class ArtifactProposal(BaseModel):
    name: str
    content: str
    content_type: str = "text/markdown"


class NotificationRequest(BaseModel):
    importance: InterruptionPolicy
    message: str


class AgentOutput(BaseModel):
    """Validated against this schema before any action is executed."""

    # Relevance gate (spec: an agent must stay silent unless its lens genuinely applies —
    # with many agents and a high volume of thoughts, always responding is noise, not signal).
    relevant: bool = True
    skip_reason: str = ""

    message: str = ""
    memory_updates: list[MemoryUpdate] = Field(default_factory=list)
    tasks: list[TaskProposal] = Field(default_factory=list)
    research_jobs: list[ResearchJobProposal] = Field(default_factory=list)
    project_updates: list[ProjectUpdate] = Field(default_factory=list)
    questions_for_user: list[QuestionForUser] = Field(default_factory=list)
    connections: list[ConnectionProposal] = Field(default_factory=list)
    artifacts: list[ArtifactProposal] = Field(default_factory=list)
    notification_request: NotificationRequest | None = None
