from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import AgentDispatchStatus
from app.db.session import get_db
from app.models.agent import Agent
from app.models.dispatch import AgentDispatch
from app.models.memory import Memory
from app.models.research import ResearchJob
from app.models.task import Task
from app.schemas.common import ORMModel

router = APIRouter(prefix="/api/agents", tags=["agents"])


class AgentOut(ORMModel):
    id: str
    name: str
    slug: str
    description: str
    icon: str
    accent: str
    system_role: str
    provider: str
    model: str
    autonomy_level: int
    interruption_policy: str
    is_supervisor: bool
    enabled: bool
    routing_keywords: str


class AgentUpdate(BaseModel):
    enabled: bool | None = None
    autonomy_level: int | None = None
    interruption_policy: str | None = None
    model: str | None = None
    system_role: str | None = None


async def _status_for(db: AsyncSession, agent_id: str) -> str:
    working = (
        await db.execute(
            select(func.count(AgentDispatch.id)).where(
                AgentDispatch.agent_id == agent_id,
                AgentDispatch.status == AgentDispatchStatus.PROCESSING.value,
            )
        )
    ).scalar() or 0
    return "working" if working else "idle"


@router.get("")
async def list_agents(db: AsyncSession = Depends(get_db)):
    agents = (await db.execute(select(Agent).order_by(Agent.is_supervisor, Agent.name))).scalars().all()
    out = []
    for a in agents:
        unread = (
            await db.execute(
                select(func.count(AgentDispatch.id)).where(
                    AgentDispatch.agent_id == a.id, AgentDispatch.read.is_(False)
                )
            )
        ).scalar() or 0
        active = (
            await db.execute(
                select(func.count(AgentDispatch.id)).where(
                    AgentDispatch.agent_id == a.id,
                    AgentDispatch.status.in_(
                        [AgentDispatchStatus.PROCESSING.value, AgentDispatchStatus.WAITING_FOR_USER.value]
                    ),
                )
            )
        ).scalar() or 0
        out.append(
            {
                **AgentOut.model_validate(a).model_dump(),
                "status": await _status_for(db, a.id),
                "unread_count": int(unread),
                "active_work_count": int(active),
            }
        )
    return {"items": out}


@router.get("/{agent_id}")
async def get_agent(agent_id: str, db: AsyncSession = Depends(get_db)):
    a = await _resolve(db, agent_id)
    return AgentOut.model_validate(a)


@router.patch("/{agent_id}")
async def update_agent(agent_id: str, body: AgentUpdate, db: AsyncSession = Depends(get_db)):
    a = await _resolve(db, agent_id)
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(a, k, v)
    await db.flush()
    return AgentOut.model_validate(a)


@router.get("/{agent_id}/inbox")
async def agent_inbox(agent_id: str, db: AsyncSession = Depends(get_db)):
    a = await _resolve(db, agent_id)
    rows = (
        await db.execute(
            select(AgentDispatch)
            .where(AgentDispatch.agent_id == a.id)
            .order_by(AgentDispatch.created_at.desc())
            .limit(100)
        )
    ).scalars().all()
    return {
        "items": [
            {
                "id": d.id,
                "thought_id": d.thought_id,
                "status": d.status,
                "response_mode": d.response_mode,
                "response_summary": d.response_summary,
                "read": d.read,
                "created_at": d.created_at,
            }
            for d in rows
        ]
    }


@router.get("/{agent_id}/memory")
async def agent_memory(agent_id: str, db: AsyncSession = Depends(get_db)):
    a = await _resolve(db, agent_id)
    rows = (
        await db.execute(
            select(Memory).where(Memory.agent_id == a.id).order_by(Memory.created_at.desc())
        )
    ).scalars().all()
    return {
        "items": [
            {
                "id": m.id,
                "category": m.category,
                "content": m.content,
                "originating_thought_id": m.originating_thought_id,
                "created_at": m.created_at,
            }
            for m in rows
        ]
    }


@router.get("/{agent_id}/tasks")
async def agent_tasks(agent_id: str, db: AsyncSession = Depends(get_db)):
    a = await _resolve(db, agent_id)
    rows = (
        await db.execute(select(Task).where(Task.created_by_agent_id == a.id))
    ).scalars().all()
    return {"items": [{"id": t.id, "title": t.title, "status": t.status, "priority": t.priority} for t in rows]}


@router.get("/{agent_id}/overview")
async def agent_overview(agent_id: str, db: AsyncSession = Depends(get_db)):
    a = await _resolve(db, agent_id)
    recent_memories = (
        await db.execute(
            select(Memory).where(Memory.agent_id == a.id).order_by(Memory.created_at.desc()).limit(5)
        )
    ).scalars().all()
    tasks = (await db.execute(select(Task).where(Task.created_by_agent_id == a.id).limit(10))).scalars().all()
    research = (
        await db.execute(select(ResearchJob).where(ResearchJob.agent_id == a.id).limit(10))
    ).scalars().all()
    return {
        "agent": AgentOut.model_validate(a),
        "status": await _status_for(db, a.id),
        "recent_memory": [{"id": m.id, "category": m.category, "content": m.content} for m in recent_memories],
        "tasks": [{"id": t.id, "title": t.title, "status": t.status} for t in tasks],
        "research_jobs": [{"id": r.id, "question": r.question, "status": r.status} for r in research],
    }


async def _resolve(db: AsyncSession, agent_id: str) -> Agent:
    a = await db.get(Agent, agent_id)
    if not a:
        a = (await db.execute(select(Agent).where(Agent.slug == agent_id))).scalars().first()
    if not a:
        raise HTTPException(404, "agent not found")
    return a
