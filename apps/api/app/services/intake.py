"""Intake pipeline (spec §6): audio -> store -> STT -> raw transcript -> refine -> structure ->
routing recommendations -> ready for review.

Never overwrites the original audio or raw transcript. Each failure mode leaves the thought
recoverable (status FAILED with an error in meta) rather than losing it.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import CaptureMode, ThoughtStatus
from app.core.ids import thought_id as new_thought_id
from app.core.logging import get_logger
from app.integrations.factory import get_providers
from app.models.thought import Thought
from app.services.activity import record_activity
from app.services.routing import RoutingService
from app.services.thought_refiner import ThoughtRefinerService

log = get_logger("council.intake")


class IntakeService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.providers = get_providers()
        self.refiner = ThoughtRefinerService(
            self.providers.llm, mock=self.providers.settings.is_mock
        )
        self.routing = RoutingService(db)

    async def capture_audio(
        self, *, user_id: str, audio_bytes: bytes, filename: str, source: str = "app"
    ) -> Thought:
        tid = new_thought_id()
        thought = Thought(
            id=tid,
            user_id=user_id,
            source=source,
            capture_mode=CaptureMode.VOICE.value,
            status=ThoughtStatus.TRANSCRIBING.value,
        )
        self.db.add(thought)
        await self.db.flush()

        # 1) Store original audio permanently.
        key = f"audio/{tid}/{filename or 'recording.webm'}"
        try:
            uri = await self.providers.storage.put(key, audio_bytes, content_type="audio/webm")
            thought.original_audio_uri = uri
        except Exception as exc:
            log.error("audio_store_failed", error=str(exc))
            thought.meta = {**thought.meta, "audio_store_error": str(exc)}

        # 2) Transcribe (never overwrites — raw_transcript set once).
        try:
            result = await self.providers.transcription.transcribe(audio_bytes, filename=filename)
            thought.raw_transcript = result.text
            thought.audio_duration = result.duration
        except Exception as exc:
            log.error("transcription_failed", error=str(exc))
            thought.status = ThoughtStatus.FAILED.value
            thought.meta = {**thought.meta, "stt_error": str(exc)}
            await record_activity(
                self.db, kind="intake", level="error",
                message="Transcription failed; original audio preserved.",
                links=[{"type": "thought", "id": tid, "label": "thought"}],
            )
            return thought

        return await self._refine_and_structure(thought)

    async def capture_text(self, *, user_id: str, text: str, title: str | None, source: str) -> Thought:
        thought = Thought(
            user_id=user_id,
            source=source,
            capture_mode=CaptureMode.TEXT.value,
            raw_transcript=text,
            status=ThoughtStatus.REFINING.value,
        )
        self.db.add(thought)
        await self.db.flush()
        if title:
            thought.title = title
        return await self._refine_and_structure(thought)

    async def _refine_and_structure(self, thought: Thought) -> Thought:
        thought.status = ThoughtStatus.REFINING.value
        try:
            refined = await self.refiner.refine(thought.raw_transcript)
        except Exception as exc:
            log.error("refine_failed", error=str(exc))
            # Degrade gracefully: keep raw as clean so the thought is still usable.
            thought.clean_transcript = thought.raw_transcript
            thought.status = ThoughtStatus.READY_FOR_REVIEW.value
            thought.meta = {**thought.meta, "refine_error": str(exc)}
            return thought

        thought.clean_transcript = refined.clean_transcript
        if thought.title in ("Untitled thought", "") or thought.capture_mode == "voice":
            thought.title = refined.title
        thought.summary = refined.summary
        thought.thought_type = refined.thought_type.value
        thought.topics = refined.topics
        thought.entities = refined.entities
        thought.questions = refined.questions
        thought.ideas = refined.ideas
        thought.possible_actions = refined.possible_actions
        thought.importance = refined.importance
        thought.urgency = refined.urgency

        # Routing recommendations.
        suggestions = await self.routing.suggest(
            text=f"{thought.clean_transcript} {' '.join(thought.topics)}",
            topics=thought.topics,
        )
        thought.routing_suggestions = [s.model_dump() for s in suggestions]
        thought.status = ThoughtStatus.READY_FOR_REVIEW.value

        # Optional embedding for semantic search (mock embeddings are offline).
        try:
            vectors = await self.providers.embeddings.embed([thought.clean_transcript])
            thought.embedding = vectors[0]
        except Exception as exc:
            log.warning("embed_failed", error=str(exc))

        await record_activity(
            self.db,
            kind="intake",
            message=f"Thought processed: “{thought.title}”",
            links=[{"type": "thought", "id": thought.id, "label": thought.title}],
        )
        return thought
