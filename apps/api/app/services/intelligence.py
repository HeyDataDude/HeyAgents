"""Cross-agent intelligence (spec §17).

Discovers connections between objects WITH explainable provenance. Never fabricates relationships
just to show activity — every connection records exactly which objects it links and why.

Heuristics implemented:
  - shared theme across thoughts (topic co-occurrence)
  - related thoughts (embedding cosine similarity when available, else topic Jaccard)
  - duplicate tasks (title similarity)
Each is cheap, deterministic and explainable; an LLM pass can refine them later behind this API.
"""

from __future__ import annotations

import math
import re

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import ConnectionType
from app.models.connection import Connection
from app.models.task import Task
from app.models.thought import Thought
from app.services.activity import record_activity


class IntelligenceService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(self, *, limit_thoughts: int = 100) -> list[Connection]:
        thoughts = (
            await self.db.execute(
                select(Thought).order_by(Thought.created_at.desc()).limit(limit_thoughts)
            )
        ).scalars().all()
        found: list[Connection] = []
        found += await self._shared_themes(thoughts)
        found += await self._related_thoughts(thoughts)
        found += await self._duplicate_tasks()
        if found:
            await record_activity(
                self.db, kind="intelligence", actor="cross-agent",
                message=f"Discovered {len(found)} cross-agent connection(s)",
                links=[],
            )
        return found

    async def _shared_themes(self, thoughts: list[Thought]) -> list[Connection]:
        by_topic: dict[str, list[Thought]] = {}
        for t in thoughts:
            for topic in t.topics or []:
                by_topic.setdefault(topic, []).append(t)
        out: list[Connection] = []
        for topic, group in by_topic.items():
            if len(group) >= 3:
                related = [{"type": "thought", "id": t.id, "label": t.title} for t in group[:6]]
                conn = await self._upsert(
                    key=f"theme:{topic}",
                    type_=ConnectionType.SHARED_THEME,
                    title=f"Recurring theme: {topic}",
                    explanation=(
                        f"{len(group)} thoughts share the topic “{topic}”: "
                        + ", ".join(f"“{t.title}”" for t in group[:4])
                    ),
                    confidence=min(0.95, 0.5 + 0.1 * len(group)),
                    related=related,
                )
                if conn:
                    out.append(conn)
        return out

    async def _related_thoughts(self, thoughts: list[Thought]) -> list[Connection]:
        out: list[Connection] = []
        for i in range(len(thoughts)):
            for j in range(i + 1, len(thoughts)):
                a, b = thoughts[i], thoughts[j]
                sim = _similarity(a, b)
                if sim >= 0.78:
                    conn = await self._upsert(
                        key=f"related:{min(a.id, b.id)}:{max(a.id, b.id)}",
                        type_=ConnectionType.RELATED_THOUGHT,
                        title=f"Related: “{a.title}” ↔ “{b.title}”",
                        explanation=f"High content similarity ({sim:.2f}).",
                        confidence=round(sim, 2),
                        related=[
                            {"type": "thought", "id": a.id, "label": a.title},
                            {"type": "thought", "id": b.id, "label": b.title},
                        ],
                    )
                    if conn:
                        out.append(conn)
        return out

    async def _duplicate_tasks(self) -> list[Connection]:
        tasks = (await self.db.execute(select(Task))).scalars().all()
        out: list[Connection] = []
        for i in range(len(tasks)):
            for j in range(i + 1, len(tasks)):
                a, b = tasks[i], tasks[j]
                if _title_similarity(a.title, b.title) >= 0.8:
                    conn = await self._upsert(
                        key=f"dup:{min(a.id, b.id)}:{max(a.id, b.id)}",
                        type_=ConnectionType.DUPLICATE_TASK,
                        title="Possible duplicate tasks",
                        explanation=f"“{a.title}” and “{b.title}” look like duplicates.",
                        confidence=0.8,
                        related=[
                            {"type": "task", "id": a.id, "label": a.title},
                            {"type": "task", "id": b.id, "label": b.title},
                        ],
                    )
                    if conn:
                        out.append(conn)
        return out

    async def _upsert(self, *, key, type_, title, explanation, confidence, related):
        existing = (
            await self.db.execute(
                select(Connection).where(Connection.title == title)
            )
        ).scalars().first()
        if existing:
            return None
        conn = Connection(
            type=type_.value,
            title=title,
            explanation=explanation,
            confidence=confidence,
            related_objects=related,
            discovered_by="cross-agent",
        )
        self.db.add(conn)
        await self.db.flush()
        return conn


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z]{3,}", (text or "").lower()))


def _title_similarity(a: str, b: str) -> float:
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def _similarity(a: Thought, b: Thought) -> float:
    # Prefer embedding cosine if both present.
    va, vb = getattr(a, "embedding", None), getattr(b, "embedding", None)
    if isinstance(va, list) and isinstance(vb, list) and len(va) == len(vb) and va:
        dot = sum(x * y for x, y in zip(va, vb))
        na = math.sqrt(sum(x * x for x in va)) or 1
        nb = math.sqrt(sum(y * y for y in vb)) or 1
        return dot / (na * nb)
    # Fall back to topic + text Jaccard.
    ta = _tokens(a.clean_transcript) | set(a.topics or [])
    tb = _tokens(b.clean_transcript) | set(b.topics or [])
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)
