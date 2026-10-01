"""Domain-wide enumerations. These are the shared vocabulary of Council.

The frontend mirrors these in `packages/shared/src/enums.ts` — keep them in sync.
"""

from __future__ import annotations

from enum import Enum


class StrEnum(str, Enum):
    def __str__(self) -> str:  # pragma: no cover - cosmetic
        return self.value


class ThoughtType(StrEnum):
    IDEA = "idea"
    QUESTION = "question"
    OBSERVATION = "observation"
    REFLECTION = "reflection"
    TASK = "task"
    DECISION = "decision"
    NOTE = "note"


class ThoughtStatus(StrEnum):
    CAPTURED = "captured"
    TRANSCRIBING = "transcribing"
    REFINING = "refining"
    READY_FOR_REVIEW = "ready_for_review"
    DISPATCHED = "dispatched"
    FAILED = "failed"


class CaptureMode(StrEnum):
    VOICE = "voice"
    TEXT = "text"
    IMPORT = "import"


class ResponseMode(StrEnum):
    TALK = "talk"
    QUICK = "quick"
    DEEP = "deep"
    REMEMBER = "remember"
    AUTO = "auto"


class RoutingMode(StrEnum):
    MANUAL = "manual"
    SUGGESTED = "suggested"
    AUTOMATIC = "automatic"


class DispatchStatus(StrEnum):
    PENDING = "pending"
    DISPATCHED = "dispatched"
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"


class AgentDispatchStatus(StrEnum):
    QUEUED = "queued"
    PROCESSING = "processing"
    WAITING_FOR_USER = "waiting_for_user"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AutonomyLevel(int, Enum):
    OBSERVE = 0
    RECOMMEND = 1
    CREATE_INTERNAL = 2
    EXTERNAL_WITH_APPROVAL = 3
    EXTERNAL_WHITELISTED = 4


class InterruptionPolicy(StrEnum):
    URGENT = "urgent"
    IMPORTANT_TIME_SENSITIVE = "important_time_sensitive"
    NEEDS_DECISION = "needs_decision"
    USEFUL = "useful"
    NORMAL = "normal"
    LOW_VALUE = "low_value"
    MEMORY_ONLY = "memory_only"


class MemoryScope(StrEnum):
    GLOBAL = "global"
    AGENT = "agent"
    PROJECT = "project"


class TaskStatus(StrEnum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    DONE = "done"
    CANCELLED = "cancelled"


class Priority(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class ProjectStatus(StrEnum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class ResearchStatus(StrEnum):
    QUEUED = "queued"
    RESEARCHING = "researching"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ReportType(StrEnum):
    MORNING = "morning"
    DAILY = "daily"
    WEEKLY = "weekly"
    AGENT = "agent"
    RESEARCH = "research"
    CUSTOM = "custom"


class QuestionStatus(StrEnum):
    OPEN = "open"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class JobStatus(StrEnum):
    QUEUED = "queued"
    WORKING = "working"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ConnectionType(StrEnum):
    SHARED_THEME = "shared_theme"
    RELATED_THOUGHT = "related_thought"
    AGENT_DISAGREEMENT = "agent_disagreement"
    DUPLICATE_TASK = "duplicate_task"
    CONTRADICTION = "contradiction"
    PROJECT_LINK = "project_link"
    IDEA_EVOLUTION = "idea_evolution"


class MessageRole(StrEnum):
    USER = "user"
    AGENT = "agent"
    SYSTEM = "system"
    MODERATOR = "moderator"
