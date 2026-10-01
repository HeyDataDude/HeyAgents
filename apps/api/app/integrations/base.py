"""Provider interfaces (abstractions) for every external capability.

Council is never tightly coupled to one vendor. Each capability has:
  - an abstract Protocol/ABC defining the interface,
  - a mock implementation (deterministic, offline, no keys),
  - optional live adapters (OpenAI, faster-whisper, Letta, LiveKit, S3, ...).

The factory in `app.integrations.factory` picks the implementation from settings.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass, field


# ── Transcription (STT) ─────────────────────────────────────────────────────────
@dataclass
class TranscriptSegment:
    start: float
    end: float
    text: str
    speaker: str | None = None


@dataclass
class TranscriptionResult:
    text: str
    duration: float
    language: str = "en"
    segments: list[TranscriptSegment] = field(default_factory=list)


class TranscriptionProvider(abc.ABC):
    name: str = "base"

    @abc.abstractmethod
    async def transcribe(self, audio_bytes: bytes, *, filename: str = "audio") -> TranscriptionResult:
        ...


# ── LLM ───────────────────────────────────────────────────────────────────────
@dataclass
class LLMMessage:
    role: str
    content: str


class LLMProvider(abc.ABC):
    name: str = "base"

    @abc.abstractmethod
    async def complete(
        self, messages: list[LLMMessage], *, model: str | None = None, temperature: float = 0.4
    ) -> str:
        ...

    @abc.abstractmethod
    async def complete_json(
        self, messages: list[LLMMessage], *, model: str | None = None
    ) -> dict:
        ...


# ── Embeddings ──────────────────────────────────────────────────────────────────
class EmbeddingProvider(abc.ABC):
    name: str = "base"
    dim: int = 1536

    @abc.abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]:
        ...


# ── TTS ─────────────────────────────────────────────────────────────────────────
class TTSProvider(abc.ABC):
    name: str = "base"

    @abc.abstractmethod
    async def synthesize(self, text: str, *, voice: str | None = None) -> bytes:
        ...


# ── Web / research ───────────────────────────────────────────────────────────────
@dataclass
class ResearchSource:
    title: str
    url: str
    snippet: str


class ResearchProvider(abc.ABC):
    name: str = "base"

    @abc.abstractmethod
    async def search(self, query: str, *, max_results: int = 5) -> list[ResearchSource]:
        ...


# ── Persistent agent memory (Letta) ──────────────────────────────────────────────
class AgentMemoryProvider(abc.ABC):
    """Maps Council agents onto stateful persistent agents (e.g. Letta)."""

    name: str = "base"

    @abc.abstractmethod
    async def ensure_agent(self, slug: str, *, system_role: str, model: str) -> str:
        """Return the external agent id, creating it if needed."""

    @abc.abstractmethod
    async def send(self, external_agent_id: str, message: str) -> str:
        """Send a message to the persistent agent and return its reply text."""


# ── Realtime voice (LiveKit / Pipecat) ────────────────────────────────────────────
@dataclass
class RealtimeSession:
    room: str
    token: str
    url: str
    provider: str


class RealtimeVoiceProvider(abc.ABC):
    name: str = "base"

    @abc.abstractmethod
    async def create_session(self, *, identity: str, room: str) -> RealtimeSession:
        ...


# ── Object storage ───────────────────────────────────────────────────────────────
class StorageProvider(abc.ABC):
    name: str = "base"

    @abc.abstractmethod
    async def put(self, key: str, data: bytes, *, content_type: str = "application/octet-stream") -> str:
        """Store bytes and return a URI."""

    @abc.abstractmethod
    async def get(self, key: str) -> bytes:
        ...

    @abc.abstractmethod
    def url_for(self, key: str) -> str:
        ...
