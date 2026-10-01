from __future__ import annotations

import pytest

from app.services.routing import RoutingService


@pytest.mark.asyncio
async def test_routing_recommends_relevant_agents(db, seeded):
    svc = RoutingService(db)
    suggestions = await svc.suggest(
        text="why do people not shower, depression, hygiene, behavior, content idea",
        topics=["hygiene", "behavior", "content"],
    )
    assert suggestions
    # Sorted by confidence desc.
    confidences = [s.confidence for s in suggestions]
    assert confidences == sorted(confidences, reverse=True)
    slugs = [s.agent_slug for s in suggestions[:4]]
    # Research/Behavior/Content should rank near the top for this thought.
    assert any(s in slugs for s in ("research", "behavior", "content"))
    # Career should score low / not be top.
    career = next((s for s in suggestions if s.agent_slug == "career"), None)
    if career:
        assert career.confidence < max(confidences)


@pytest.mark.asyncio
async def test_auto_recipients_threshold(db, seeded):
    svc = RoutingService(db)
    suggestions = await svc.suggest(text="build an app project mvp feature ship code", topics=["build", "app"])
    chosen = RoutingService.auto_recipients(suggestions, threshold=0.6)
    assert isinstance(chosen, list)
