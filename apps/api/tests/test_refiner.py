from __future__ import annotations

import pytest

from app.integrations.mock import MockLLMProvider
from app.services.thought_refiner import RefinedThought, ThoughtRefinerService

RAW = (
    "I don't know, I was thinking today, um, why do some people just not shower? Like maybe "
    "depression is part of it, but maybe some people genuinely don't think about hygiene the same "
    "way. Could be a content idea too."
)


@pytest.mark.asyncio
async def test_refiner_schema_and_meaning_preservation():
    svc = ThoughtRefinerService(MockLLMProvider(), mock=True)
    refined = await svc.refine(RAW)

    assert isinstance(refined, RefinedThought)
    # Filler removed.
    assert " um," not in refined.clean_transcript.lower()
    assert "um " not in refined.clean_transcript.lower()
    # Uncertainty preserved — must NOT become a confident fact.
    assert "maybe" in refined.clean_transcript.lower()
    # Structure extracted.
    assert refined.title
    assert refined.summary
    assert len(refined.topics) >= 1
    # The "content idea" hint should surface as an idea/action.
    joined = " ".join(refined.ideas + refined.possible_actions).lower()
    assert "content" in joined or any("content" in t for t in refined.topics)


@pytest.mark.asyncio
async def test_refiner_detects_questions():
    svc = ThoughtRefinerService(MockLLMProvider(), mock=True)
    refined = await svc.refine("Why does sleep timing matter? How should I schedule my day?")
    assert len(refined.questions) >= 1
