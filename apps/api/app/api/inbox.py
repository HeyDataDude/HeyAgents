from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import AgentDispatchStatus, QuestionStatus
from app.db.session import get_db
from app.models.agent import Agent
from app.models.dispatch import AgentDispatch
from app.models.question import AgentQuestion

router = APIRouter(prefix="/api/inbox", tags=["inbox"])


class AnswerQuestion(BaseModel):
    answer: str


@router.get("")
async def get_inbox(db: AsyncSession = Depends(get_db), filter: str = "all"):
    """Aggregates everything requiring user attention (spec §27)."""
    agents = {a.id: a for a in (await db.execute(select(Agent))).scalars()}
    items: list[dict] = []

    if filter in ("all", "needs_decision", "agent_questions"):
        questions = (
            await db.execute(
                select(AgentQuestion).where(AgentQuestion.status == QuestionStatus.OPEN.value)
            )
        ).scalars().all()
        for q in questions:
            a = agents.get(q.agent_id)
            items.append({
                "kind": "agent_question",
                "id": q.id,
                "title": q.question,
                "context": q.context,
                "agent": a.name if a else q.agent_id,
                "importance": q.importance,
                "created_at": q.created_at,
            })

    if filter in ("all", "needs_review", "completed_work"):
        waiting = (
            await db.execute(
                select(AgentDispatch).where(
                    AgentDispatch.status.in_(
                        [AgentDispatchStatus.WAITING_FOR_USER.value, AgentDispatchStatus.COMPLETED.value]
                    ),
                    AgentDispatch.read.is_(False),
                ).order_by(AgentDispatch.created_at.desc()).limit(50)
            )
        ).scalars().all()
        for d in waiting:
            a = agents.get(d.agent_id)
            items.append({
                "kind": "needs_review" if d.status == AgentDispatchStatus.WAITING_FOR_USER.value else "completed_work",
                "id": d.id,
                "title": d.response_summary or "Agent response",
                "agent": a.name if a else d.agent_id,
                "thought_id": d.thought_id,
                "status": d.status,
                "created_at": d.created_at,
            })

    if filter in ("all", "failures"):
        failed = (
            await db.execute(
                select(AgentDispatch).where(AgentDispatch.status == AgentDispatchStatus.FAILED.value)
            )
        ).scalars().all()
        for d in failed:
            items.append({
                "kind": "failure",
                "id": d.id,
                "title": f"Agent run failed: {d.error}",
                "thought_id": d.thought_id,
                "created_at": d.created_at,
            })

    items.sort(key=lambda i: i["created_at"], reverse=True)
    return {"items": items}


@router.post("/questions/{question_id}/answer")
async def answer_question(question_id: str, body: AnswerQuestion, db: AsyncSession = Depends(get_db)):
    q = await db.get(AgentQuestion, question_id)
    if not q:
        raise HTTPException(404, "question not found")
    q.answer = body.answer
    q.status = QuestionStatus.RESOLVED.value
    q.resolved_at = datetime.now(UTC)
    await db.flush()
    return {"id": q.id, "status": q.status}


@router.post("/dispatches/{agent_dispatch_id}/read")
async def mark_read(agent_dispatch_id: str, db: AsyncSession = Depends(get_db)):
    d = await db.get(AgentDispatch, agent_dispatch_id)
    if not d:
        raise HTTPException(404, "agent dispatch not found")
    d.read = True
    await db.flush()
    return {"id": d.id, "read": True}
