"""Live provider adapters.

These are intentionally thin: Council owns the orchestration; the vendor owns the capability.
All heavy imports are lazy so `mock` mode never requires these packages. Install them with the
`live` extra: `pip install -e ".[live]"`.

Integration decisions (see docs/architecture.md):
  - STT:          faster-whisper for recorded speech (WhisperX only when diarization helps).
  - LLM:          OpenAI-compatible (also works with Ollama / local gateways).
  - Agent memory: Letta — each Council agent maps to a persistent Letta agent.
  - Realtime:     LiveKit Agents for streaming voice (token minted here; the agent worker joins).
"""

from __future__ import annotations

from app.core.config import Settings
from app.integrations.base import (
    AgentMemoryProvider,
    EmbeddingProvider,
    LLMProvider,
    RealtimeSession,
    RealtimeVoiceProvider,
    TranscriptionProvider,
    TranscriptionResult,
    TranscriptSegment,
)


class FasterWhisperProvider(TranscriptionProvider):
    name = "faster_whisper"

    def __init__(self, settings: Settings):
        from faster_whisper import WhisperModel  # lazy

        self._model = WhisperModel(settings.stt_model, device=settings.stt_device)

    async def transcribe(self, audio_bytes: bytes, *, filename: str = "audio") -> TranscriptionResult:
        import asyncio
        import tempfile

        def _run() -> TranscriptionResult:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as f:
                f.write(audio_bytes)
                f.flush()
                segments, info = self._model.transcribe(f.name, vad_filter=True)
                segs = [TranscriptSegment(s.start, s.end, s.text.strip()) for s in segments]
            text = " ".join(s.text for s in segs).strip()
            return TranscriptionResult(
                text=text, duration=info.duration, language=info.language, segments=segs
            )

        return await asyncio.to_thread(_run)


class OpenAILLMProvider(LLMProvider):
    name = "openai"

    def __init__(self, settings: Settings):
        from openai import AsyncOpenAI  # lazy

        self._client = AsyncOpenAI(api_key=settings.openai_api_key)
        self._default = settings.llm_default_model

    async def complete(self, messages, *, model=None, temperature=0.4) -> str:
        resp = await self._client.chat.completions.create(
            model=model or self._default,
            messages=[{"role": m.role, "content": m.content} for m in messages],
            temperature=temperature,
        )
        return resp.choices[0].message.content or ""

    async def complete_json(self, messages, *, model=None) -> dict:
        import json

        resp = await self._client.chat.completions.create(
            model=model or self._default,
            messages=[{"role": m.role, "content": m.content} for m in messages],
            response_format={"type": "json_object"},
        )
        return json.loads(resp.choices[0].message.content or "{}")


class OpenAIEmbeddingProvider(EmbeddingProvider):
    name = "openai"

    def __init__(self, settings: Settings):
        from openai import AsyncOpenAI  # lazy

        self._client = AsyncOpenAI(api_key=settings.openai_api_key)
        self._model = settings.embedding_model
        self.dim = settings.embedding_dim

    async def embed(self, texts: list[str]) -> list[list[float]]:
        resp = await self._client.embeddings.create(model=self._model, input=texts)
        return [d.embedding for d in resp.data]


class LettaAgentMemoryProvider(AgentMemoryProvider):
    name = "letta"

    def __init__(self, settings: Settings):
        from letta_client import Letta  # lazy

        self._client = Letta(base_url=settings.letta_base_url, token=settings.letta_api_key)

    async def ensure_agent(self, slug: str, *, system_role: str, model: str) -> str:
        import asyncio

        def _run() -> str:
            existing = {a.name: a.id for a in self._client.agents.list()}
            if slug in existing:
                return existing[slug]
            agent = self._client.agents.create(name=slug, system=system_role, model=model)
            return agent.id

        return await asyncio.to_thread(_run)

    async def send(self, external_agent_id: str, message: str) -> str:
        import asyncio

        def _run() -> str:
            resp = self._client.agents.messages.create(
                agent_id=external_agent_id,
                messages=[{"role": "user", "content": message}],
            )
            parts = [m.content for m in resp.messages if getattr(m, "content", None)]
            return "\n".join(parts)

        return await asyncio.to_thread(_run)


class LiveKitRealtimeProvider(RealtimeVoiceProvider):
    name = "livekit"

    def __init__(self, settings: Settings):
        self._url = settings.livekit_url
        self._key = settings.livekit_api_key
        self._secret = settings.livekit_api_secret

    async def create_session(self, *, identity: str, room: str) -> RealtimeSession:
        from livekit import api  # lazy

        token = (
            api.AccessToken(self._key, self._secret)
            .with_identity(identity)
            .with_grants(api.VideoGrants(room_join=True, room=room))
            .to_jwt()
        )
        return RealtimeSession(room=room, token=token, url=self._url or "", provider="livekit")
