"""Provider factory: resolves the configured implementation for each capability.

In `mock` mode (default) everything is offline. In `live` mode each provider is chosen by its
own setting, so you can mix (e.g. real STT + mock LLM) while bringing up integrations.
"""

from __future__ import annotations

from functools import lru_cache

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.integrations import mock
from app.integrations.base import (
    AgentMemoryProvider,
    EmbeddingProvider,
    LLMProvider,
    RealtimeVoiceProvider,
    ResearchProvider,
    StorageProvider,
    TranscriptionProvider,
    TTSProvider,
)
from app.integrations.storage import LocalStorageProvider, S3StorageProvider

log = get_logger("council.providers")


def _is_mock(settings: Settings, provider_value: str) -> bool:
    return settings.is_mock or provider_value == "mock"


def build_transcription(settings: Settings) -> TranscriptionProvider:
    if _is_mock(settings, settings.stt_provider):
        return mock.MockTranscriptionProvider()
    if settings.stt_provider in ("faster_whisper", "whisperx"):
        from app.integrations.live import FasterWhisperProvider

        return FasterWhisperProvider(settings)
    log.warning("unknown_stt_provider_fallback_mock", provider=settings.stt_provider)
    return mock.MockTranscriptionProvider()


def build_llm(settings: Settings) -> LLMProvider:
    if _is_mock(settings, settings.llm_provider):
        return mock.MockLLMProvider()
    if settings.llm_provider == "openai":
        from app.integrations.live import OpenAILLMProvider

        return OpenAILLMProvider(settings)
    log.warning("unknown_llm_provider_fallback_mock", provider=settings.llm_provider)
    return mock.MockLLMProvider()


def build_embeddings(settings: Settings) -> EmbeddingProvider:
    if _is_mock(settings, settings.embedding_provider):
        return mock.MockEmbeddingProvider(settings.embedding_dim)
    if settings.embedding_provider == "openai":
        from app.integrations.live import OpenAIEmbeddingProvider

        return OpenAIEmbeddingProvider(settings)
    return mock.MockEmbeddingProvider(settings.embedding_dim)


def build_tts(settings: Settings) -> TTSProvider:
    # Only a mock TTS ships by default; live adapters follow the same pattern.
    return mock.MockTTSProvider()


def build_research(settings: Settings) -> ResearchProvider:
    if _is_mock(settings, settings.research_provider):
        return mock.MockResearchProvider()
    return mock.MockResearchProvider()


def build_agent_memory(settings: Settings) -> AgentMemoryProvider:
    if _is_mock(settings, settings.agent_memory_provider):
        return mock.MockAgentMemoryProvider()
    if settings.agent_memory_provider == "letta":
        from app.integrations.live import LettaAgentMemoryProvider

        return LettaAgentMemoryProvider(settings)
    return mock.MockAgentMemoryProvider()


def build_realtime(settings: Settings) -> RealtimeVoiceProvider:
    if _is_mock(settings, settings.realtime_provider):
        return mock.MockRealtimeVoiceProvider()
    if settings.realtime_provider == "livekit":
        from app.integrations.live import LiveKitRealtimeProvider

        return LiveKitRealtimeProvider(settings)
    return mock.MockRealtimeVoiceProvider()


def build_storage(settings: Settings) -> StorageProvider:
    if settings.storage_backend == "s3":
        return S3StorageProvider(settings)
    return LocalStorageProvider(settings.storage_local_dir)


class Providers:
    """Bundle of all resolved providers, built once per process."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.transcription = build_transcription(settings)
        self.llm = build_llm(settings)
        self.embeddings = build_embeddings(settings)
        self.tts = build_tts(settings)
        self.research = build_research(settings)
        self.agent_memory = build_agent_memory(settings)
        self.realtime = build_realtime(settings)
        self.storage = build_storage(settings)

    def health(self) -> dict[str, str]:
        return {
            "mode": self.settings.provider_mode,
            "transcription": self.transcription.name,
            "llm": self.llm.name,
            "embeddings": self.embeddings.name,
            "tts": self.tts.name,
            "research": self.research.name,
            "agent_memory": self.agent_memory.name,
            "realtime": self.realtime.name,
            "storage": self.storage.name,
        }


@lru_cache
def get_providers() -> Providers:
    return Providers(get_settings())
