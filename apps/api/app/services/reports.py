"""Chief of Staff reporting (spec §6, §18).

Generates Morning Brief, Daily Council Brief and Weekly Synthesis from REAL database state (never
fabricated). Reports are structured (section-based) so the UI can render and link to evidence.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import (
    AgentDispatchStatus,
    QuestionStatus,
    ReportType,
    ResearchStatus,
    TaskStatus,
)
from app.models.agent import Agent
from app.models.connection import Connection
from app.models.dispatch import AgentDispatch
from app.models.memory import Memory
from app.models.question import AgentQuestion
from app.models.report import Report
from app.models.research import ResearchJob
from app.models.task import Task
from app.models.thought import Thought
from app.services.activity import record_activity


class ReportService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _count(self, stmt) -> int:
        return int((await self.db.execute(stmt)).scalar() or 0)

    async def generate_daily(self, *, now: datetime | None = None) -> Report:
        now = now or datetime.now(UTC)
        start = now - timedelta(days=1)

        thoughts = await self._count(
            select(func.count(Thought.id)).where(Thought.created_at >= start)
        )
        runs = await self._count(
            select(func.count(AgentDispatch.id)).where(AgentDispatch.created_at >= start)
        )
        agents_involved = await self._count(
            select(func.count(func.distinct(AgentDispatch.agent_id))).where(
                AgentDispatch.created_at >= start
            )
        )
        tasks_created = await self._count(
            select(func.count(Task.id)).where(Task.created_at >= start)
        )
        connections = (
            await self.db.execute(
                select(Connection).where(Connection.created_at >= start).limit(10)
            )
        ).scalars().all()
        open_questions = (
            await self.db.execute(
                select(AgentQuestion).where(AgentQuestion.status == QuestionStatus.OPEN.value)
            )
        ).scalars().all()
        deep_done = (
            await self.db.execute(
                select(ResearchJob)
                .where(ResearchJob.status == ResearchStatus.COMPLETED.value)
                .limit(10)
            )
        ).scalars().all()
        new_tasks = (
            await self.db.execute(
                select(Task).where(Task.created_at >= start).limit(15)
            )
        ).scalars().all()
        memory_changes = await self._count(
            select(func.count(Memory.id)).where(Memory.created_at >= start)
        )

        content = {
            "headline": {
                "thoughts_captured": thoughts,
                "agents_involved": agents_involved,
                "agent_runs": runs,
                "tasks_created": tasks_created,
                "connections_discovered": len(connections),
                "decisions_required": len(open_questions),
            },
            "needs_you": [
                {"type": "question", "id": q.id, "label": q.question, "importance": q.importance}
                for q in open_questions[:8]
            ],
            "important_discoveries": [
                {"type": "connection", "id": c.id, "label": c.title, "confidence": c.confidence}
                for c in connections
            ],
            "deep_work_completed": [
                {"type": "research", "id": r.id, "label": r.question} for r in deep_done
            ],
            "new_tasks": [
                {"type": "task", "id": t.id, "label": t.title, "priority": t.priority}
                for t in new_tasks
            ],
            "memory_changes": memory_changes,
        }

        report = Report(
            type=ReportType.DAILY.value,
            title=f"Daily Council Brief — {now:%b %d, %Y}",
            range_start=start,
            range_end=now,
            content=content,
            related_objects=content["needs_you"] + content["important_discoveries"],
        )
        self.db.add(report)
        await self.db.flush()
        await record_activity(
            self.db, kind="report", actor="chief-of-staff",
            message="Chief of Staff generated the Daily Brief",
            links=[{"type": "report", "id": report.id, "label": report.title}],
        )
        return report

    async def generate_morning(self, *, now: datetime | None = None) -> Report:
        now = now or datetime.now(UTC)
        open_questions = (
            await self.db.execute(
                select(AgentQuestion).where(AgentQuestion.status == QuestionStatus.OPEN.value)
            )
        ).scalars().all()
        ready_for_review = (
            await self.db.execute(
                select(AgentDispatch).where(
                    AgentDispatch.status == AgentDispatchStatus.WAITING_FOR_USER.value
                ).limit(10)
            )
        ).scalars().all()
        overdue = (
            await self.db.execute(
                select(Task).where(
                    Task.due_at.is_not(None),
                    Task.due_at < now,
                    Task.status != TaskStatus.DONE.value,
                ).limit(10)
            )
        ).scalars().all()
        key_tasks = (
            await self.db.execute(
                select(Task).where(Task.status == TaskStatus.TODO.value).limit(8)
            )
        ).scalars().all()

        content = {
            "question": "What matters now?",
            "important_decisions": [
                {"type": "question", "id": q.id, "label": q.question} for q in open_questions[:6]
            ],
            "ready_for_review": [
                {"type": "agent_dispatch", "id": d.id, "label": d.response_summary[:80]}
                for d in ready_for_review
            ],
            "key_tasks": [{"type": "task", "id": t.id, "label": t.title} for t in key_tasks],
            "overdue": [{"type": "task", "id": t.id, "label": t.title} for t in overdue],
        }
        report = Report(
            type=ReportType.MORNING.value,
            title=f"Morning Brief — {now:%b %d, %Y}",
            range_end=now,
            content=content,
        )
        self.db.add(report)
        await self.db.flush()
        return report

    async def generate_weekly(self, *, now: datetime | None = None) -> Report:
        now = now or datetime.now(UTC)
        start = now - timedelta(days=7)

        # Theme detection via topic frequency across the week's thoughts.
        thoughts = (
            await self.db.execute(select(Thought).where(Thought.created_at >= start))
        ).scalars().all()
        topic_freq: dict[str, int] = {}
        for t in thoughts:
            for topic in t.topics or []:
                topic_freq[topic] = topic_freq.get(topic, 0) + 1
        themes = sorted(topic_freq.items(), key=lambda kv: -kv[1])[:8]

        agents = (await self.db.execute(select(Agent))).scalars().all()
        agent_names = {a.id: a.name for a in agents}
        runs_by_agent: dict[str, int] = {}
        for d in (
            await self.db.execute(
                select(AgentDispatch).where(AgentDispatch.created_at >= start)
            )
        ).scalars():
            runs_by_agent[d.agent_id] = runs_by_agent.get(d.agent_id, 0) + 1

        content = {
            "themes": [{"topic": k, "count": v} for k, v in themes],
            "thoughts_this_week": len(thoughts),
            "agent_activity": [
                {"agent": agent_names.get(aid, aid), "runs": n}
                for aid, n in sorted(runs_by_agent.items(), key=lambda kv: -kv[1])
            ],
            "momentum": _momentum(themes),
        }
        report = Report(
            type=ReportType.WEEKLY.value,
            title=f"Weekly Synthesis — week of {start:%b %d}",
            range_start=start,
            range_end=now,
            content=content,
        )
        self.db.add(report)
        await self.db.flush()
        return report


def _momentum(themes: list[tuple[str, int]]) -> dict:
    gaining = [t for t, c in themes if c >= 2]
    return {"gaining": gaining[:4], "note": "Based on repeated topics across the week."}
