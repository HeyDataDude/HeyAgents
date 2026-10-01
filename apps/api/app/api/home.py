from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import AgentDispatchStatus, QuestionStatus, ResearchStatus
from app.db.session import get_db
from app.models.agent import Agent
from app.models.connection import Connection
from app.models.dispatch import AgentDispatch
from app.models.question import AgentQuestion
from app.models.research import ResearchJob
from app.models.task import Task
from app.models.thought import Thought

router = APIRouter(prefix="/api/home", tags=["home"])


@router.get("")
async def home(db: AsyncSession = Depends(get_db)):
    """Dashboard aggregation (spec §20, §51): what needs me / what's happening / discoveries."""
    now = datetime.now(UTC)
    start = now - timedelta(hours=24)

    async def count(stmt):
        return int((await db.execute(stmt)).scalar() or 0)

    thoughts_today = await count(
        select(func.count(Thought.id)).where(Thought.created_at >= start)
    )
    active_research = await count(
        select(func.count(ResearchJob.id)).where(
            ResearchJob.status.in_([ResearchStatus.QUEUED.value, ResearchStatus.RESEARCHING.value])
        )
    )
    decisions_waiting = await count(
        select(func.count(AgentQuestion.id)).where(AgentQuestion.status == QuestionStatus.OPEN.value)
    )
    tasks_generated = await count(
        select(func.count(Task.id)).where(Task.created_at >= start)
    )

    agents = {a.id: a for a in (await db.execute(select(Agent))).scalars()}

    # Needs attention: completed/waiting dispatches that are unread.
    attention_rows = (
        await db.execute(
            select(AgentDispatch).where(
                AgentDispatch.status.in_(
                    [AgentDispatchStatus.WAITING_FOR_USER.value, AgentDispatchStatus.COMPLETED.value]
                ),
                AgentDispatch.read.is_(False),
            ).order_by(AgentDispatch.created_at.desc()).limit(6)
        )
    ).scalars().all()
    needs_attention = [
        {
            "id": d.id,
            "agent": agents[d.agent_id].name if d.agent_id in agents else d.agent_id,
            "agent_slug": agents[d.agent_id].slug if d.agent_id in agents else "",
            "summary": d.response_summary or "Response ready",
            "thought_id": d.thought_id,
            "status": d.status,
        }
        for d in attention_rows
    ]

    top_connection = (
        await db.execute(
            select(Connection).where(Connection.dismissed.is_(False)).order_by(
                Connection.confidence.desc()
            ).limit(1)
        )
    ).scalars().first()

    return {
        "today": {
            "thoughts_captured": thoughts_today,
            "active_investigations": active_research,
            "decisions_waiting": decisions_waiting,
            "tasks_generated": tasks_generated,
        },
        "needs_attention": needs_attention,
        "todays_connection": (
            {
                "id": top_connection.id,
                "title": top_connection.title,
                "explanation": top_connection.explanation,
                "confidence": top_connection.confidence,
                "related_objects": top_connection.related_objects,
            }
            if top_connection
            else None
        ),
    }
