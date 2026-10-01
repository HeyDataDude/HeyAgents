"""Routing engine (spec §8).

Recommends which specialist agents should receive a thought, with confidence scores. Supports
MANUAL / SUGGESTED / AUTOMATIC modes (default SUGGESTED). The user can always override.

The heuristic scorer matches a thought's topics/text against each agent's routing keywords and
role. It is deterministic and explainable (each suggestion carries a reason). A live LLM router can
be swapped in behind the same interface.
"""

from __future__ import annotations

import re

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent import Agent
from app.schemas.thought import RoutingSuggestion


class RoutingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def suggest(
        self, *, text: str, topics: list[str], threshold: float = 0.0
    ) -> list[RoutingSuggestion]:
        agents = (
            await self.db.execute(
                select(Agent).where(Agent.enabled.is_(True), Agent.is_supervisor.is_(False))
            )
        ).scalars().all()

        tokens = set(re.findall(r"[a-z]{3,}", text.lower())) | {t.lower() for t in topics}
        suggestions: list[RoutingSuggestion] = []
        for agent in agents:
            score, reason = self._score(agent, tokens, text)
            if score >= threshold:
                suggestions.append(
                    RoutingSuggestion(
                        agent_id=agent.id,
                        agent_slug=agent.slug,
                        agent_name=agent.name,
                        confidence=round(score, 2),
                        reason=reason,
                    )
                )
        suggestions.sort(key=lambda s: s.confidence, reverse=True)
        return suggestions

    def _score(self, agent: Agent, tokens: set[str], text: str) -> tuple[float, str]:
        keywords = {k.strip().lower() for k in agent.routing_keywords.split(",") if k.strip()}
        if not keywords:
            return 0.1, "general relevance"
        hits = sorted(tokens & keywords)
        # Base score from keyword overlap, saturating.
        overlap = len(hits)
        score = 1 - (0.65 ** overlap) if overlap else 0.04
        # Light boost if the agent's slug/name words appear in the text.
        name_words = set(re.findall(r"[a-z]{3,}", agent.name.lower()))
        if tokens & name_words:
            score = min(1.0, score + 0.15)
        reason = (
            f"matched: {', '.join(hits)}" if hits else "low topical overlap"
        )
        return round(min(score, 0.99), 2), reason

    @staticmethod
    def auto_recipients(
        suggestions: list[RoutingSuggestion], threshold: float = 0.7
    ) -> list[str]:
        return [s.agent_id for s in suggestions if s.confidence >= threshold]
