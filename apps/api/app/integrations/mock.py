"""Deterministic, offline mock providers.

These make Council fully runnable with zero API keys. They are intentionally simple but produce
realistic, schema-valid output so the entire UI and pipeline can be exercised end-to-end.
"""

from __future__ import annotations

import hashlib
import math
import re

from app.integrations.base import (
    AgentMemoryProvider,
    EmbeddingProvider,
    LLMProvider,
    RealtimeSession,
    RealtimeVoiceProvider,
    ResearchProvider,
    ResearchSource,
    TranscriptionProvider,
    TranscriptionResult,
    TranscriptSegment,
    TTSProvider,
)

_SAMPLE_TRANSCRIPT = (
    "I don't know, I was thinking today, why do some people just not shower? Like maybe "
    "depression is part of it, but maybe some people genuinely don't think about hygiene the same "
    "way. And maybe there's something broader there about things that seem obvious to one person "
    "but aren't obvious to another. Could be a content idea too."
)


class MockTranscriptionProvider(TranscriptionProvider):
    name = "mock"

    async def transcribe(self, audio_bytes: bytes, *, filename: str = "audio") -> TranscriptionResult:
        # Deterministic: estimate a duration from byte length, return the canonical sample so the
        # downstream pipeline always has rich content to work with in demo mode.
        duration = max(3.0, round(len(audio_bytes) / 16000.0, 1)) if audio_bytes else 18.0
        text = _SAMPLE_TRANSCRIPT
        return TranscriptionResult(
            text=text,
            duration=duration,
            segments=[TranscriptSegment(0.0, duration, text)],
        )


class MockLLMProvider(LLMProvider):
    name = "mock"

    async def complete(self, messages, *, model=None, temperature=0.4) -> str:
        last = messages[-1].content if messages else ""
        return (
            "Here is a concise, grounded take. I preserved the uncertainty in your thought and did "
            "not turn speculation into fact. Key angle: "
            f"{_first_sentence(last)}"
        )

    async def complete_json(self, messages, *, model=None) -> dict:
        return {"message": await self.complete(messages, model=model)}


class MockEmbeddingProvider(EmbeddingProvider):
    name = "mock"

    def __init__(self, dim: int = 1536):
        self.dim = dim

    async def embed(self, texts: list[str]) -> list[list[float]]:
        return [_hash_embedding(t, self.dim) for t in texts]


class MockTTSProvider(TTSProvider):
    name = "mock"

    async def synthesize(self, text: str, *, voice=None) -> bytes:
        # Return a tiny silent WAV header-ish placeholder; enough for the UI to "play".
        return b"RIFF\x00\x00\x00\x00WAVEfmt mock-tts:" + text[:64].encode("utf-8", "ignore")


class MockResearchProvider(ResearchProvider):
    name = "mock"

    async def search(self, query: str, *, max_results: int = 5) -> list[ResearchSource]:
        seed = _slug(query)
        return [
            ResearchSource(
                title=f"Overview: {query}"[:80],
                url=f"https://example.org/{seed}/{i}",
                snippet=(
                    f"A representative source discussing '{query}'. (mock result {i + 1}) "
                    "Replace with a live research provider by setting COUNCIL_RESEARCH_PROVIDER."
                ),
            )
            for i in range(min(max_results, 3))
        ]


class MockAgentMemoryProvider(AgentMemoryProvider):
    name = "mock"

    async def ensure_agent(self, slug: str, *, system_role: str, model: str) -> str:
        return f"mock-letta-{slug}"

    async def send(self, external_agent_id: str, message: str) -> str:
        return f"[{external_agent_id}] acknowledged: {_first_sentence(message)}"


class MockRealtimeVoiceProvider(RealtimeVoiceProvider):
    name = "mock"

    async def create_session(self, *, identity: str, room: str) -> RealtimeSession:
        return RealtimeSession(
            room=room,
            token=f"mock-token-{_slug(identity)}-{_slug(room)}",
            url="wss://mock.livekit.local",
            provider="mock",
        )


# ── helpers ──────────────────────────────────────────────────────────────────────
def _first_sentence(text: str) -> str:
    text = text.strip()
    m = re.split(r"(?<=[.!?])\s", text)
    return (m[0] if m else text)[:200]


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:40] or "x"


def _hash_embedding(text: str, dim: int) -> list[float]:
    """Deterministic pseudo-embedding: hash-seeded unit vector.

    Good enough for demo semantic search; similar strings get correlated vectors because we fold
    token hashes into dimensions.
    """
    vec = [0.0] * dim
    for token in re.findall(r"\w+", text.lower()):
        h = int(hashlib.sha1(token.encode()).hexdigest(), 16)
        idx = h % dim
        vec[idx] += 1.0 + ((h >> 8) % 7) / 10.0
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]
