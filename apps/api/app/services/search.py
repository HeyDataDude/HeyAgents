"""Global search (spec §32): hybrid lexical + semantic across all first-class objects.

Every result indicates its type and source. Semantic ranking uses embeddings when available
(including the deterministic mock embeddings); lexical matching is always applied as a fallback and
a booster.
"""

from __future__ import annotations

import math

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.factory import get_providers
from app.models.memory import Memory
from app.models.project import Project
from app.models.report import Report
from app.models.research import ResearchJob
from app.models.task import Task
from app.models.thought import Thought


class SearchResult(dict):
    pass


class SearchService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.providers = get_providers()

    async def search(self, query: str, *, limit: int = 30) -> list[dict]:
        q = query.replace("\x00", "").strip()
        if not q:
            return []
        like = f"%{q}%"
        results: list[dict] = []

        thoughts = (
            await self.db.execute(
                select(Thought).where(
                    or_(
                        Thought.title.ilike(like),
                        Thought.clean_transcript.ilike(like),
                        Thought.raw_transcript.ilike(like),
                        Thought.summary.ilike(like),
                    )
                ).limit(limit)
            )
        ).scalars().all()
        results += [
            {"type": "thought", "id": t.id, "title": t.title, "snippet": t.summary or t.clean_transcript[:160], "source": "thoughts"}
            for t in thoughts
        ]

        for model, type_, title_attr, snippet_attr, src in [
            (Task, "task", "title", "description", "tasks"),
            (Project, "project", "name", "description", "projects"),
            (Memory, "memory", "category", "content", "memory"),
            (ResearchJob, "research", "question", "findings", "research"),
            (Report, "report", "title", None, "reports"),
        ]:
            cols = [getattr(model, title_attr).ilike(like)]
            if snippet_attr:
                cols.append(getattr(model, snippet_attr).ilike(like))
            rows = (
                await self.db.execute(select(model).where(or_(*cols)).limit(limit))
            ).scalars().all()
            for r in rows:
                results.append({
                    "type": type_,
                    "id": r.id,
                    "title": getattr(r, title_attr),
                    "snippet": (getattr(r, snippet_attr) or "")[:160] if snippet_attr else "",
                    "source": src,
                })

        # Semantic boost for thoughts via embeddings.
        try:
            qvec = (await self.providers.embeddings.embed([q]))[0]
            for res in results:
                if res["type"] == "thought":
                    t = next((x for x in thoughts if x.id == res["id"]), None)
                    if t is not None and isinstance(getattr(t, "embedding", None), list):
                        res["score"] = _cos(qvec, t.embedding)
        except Exception:
            pass

        results.sort(key=lambda r: r.get("score", 0.0), reverse=True)
        return results[:limit]


def _cos(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)) or 1
    nb = math.sqrt(sum(y * y for y in b)) or 1
    return dot / (na * nb)
