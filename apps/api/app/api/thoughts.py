from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.deps import get_current_user
from app.models.dispatch import AgentDispatch
from app.models.memory import Memory
from app.models.research import ResearchJob
from app.models.task import Task
from app.models.thought import Thought
from app.models.user import User
from app.schemas.thought import (
    CreateTextThought,
    DispatchRequest,
    ThoughtOut,
    UpdateThought,
)
from app.services.dispatch import DispatchService
from app.services.intake import IntakeService

router = APIRouter(prefix="/api/thoughts", tags=["thoughts"])


@router.get("")
async def list_thoughts(
    db: AsyncSession = Depends(get_db),
    status: str | None = None,
    topic: str | None = None,
    starred: bool | None = None,
    q: str | None = None,
    limit: int = Query(50, le=200),
    offset: int = 0,
):
    stmt = select(Thought).order_by(Thought.created_at.desc())
    if status:
        stmt = stmt.where(Thought.status == status)
    if starred is not None:
        stmt = stmt.where(Thought.starred.is_(starred))
    if q:
        like = f"%{q}%"
        stmt = stmt.where(Thought.title.ilike(like) | Thought.clean_transcript.ilike(like))
    total = (await db.execute(select(func.count()).select_from(stmt.subquery()))).scalar() or 0
    rows = (await db.execute(stmt.limit(limit).offset(offset))).scalars().all()
    items = [ThoughtOut.model_validate(t) for t in rows]
    if topic:
        items = [t for t in items if topic in (t.topics or [])]
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.post("/text", response_model=ThoughtOut, status_code=201)
async def create_text_thought(
    body: CreateTextThought,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    svc = IntakeService(db)
    thought = await svc.capture_text(
        user_id=user.id, text=body.text, title=body.title, source=body.source
    )
    return ThoughtOut.model_validate(thought)


@router.post("/audio", response_model=ThoughtOut, status_code=201)
async def create_audio_thought(
    file: UploadFile = File(...),
    source: str = Form("app"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    audio_bytes = await file.read()
    svc = IntakeService(db)
    thought = await svc.capture_audio(
        user_id=user.id,
        audio_bytes=audio_bytes,
        filename=file.filename or "recording.webm",
        source=source,
    )
    return ThoughtOut.model_validate(thought)


@router.get("/{thought_id}", response_model=ThoughtOut)
async def get_thought(thought_id: str, db: AsyncSession = Depends(get_db)):
    t = await db.get(Thought, thought_id)
    if not t:
        raise HTTPException(404, "thought not found")
    return ThoughtOut.model_validate(t)


@router.patch("/{thought_id}", response_model=ThoughtOut)
async def update_thought(
    thought_id: str, body: UpdateThought, db: AsyncSession = Depends(get_db)
):
    t = await db.get(Thought, thought_id)
    if not t:
        raise HTTPException(404, "thought not found")
    data = body.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(t, key, value.value if hasattr(value, "value") else value)
    await db.flush()
    return ThoughtOut.model_validate(t)


@router.delete("/{thought_id}", status_code=204)
async def delete_thought(thought_id: str, db: AsyncSession = Depends(get_db)):
    t = await db.get(Thought, thought_id)
    if t:
        await db.delete(t)
    return None


@router.post("/{thought_id}/dispatch")
async def dispatch_thought(
    thought_id: str, body: DispatchRequest, db: AsyncSession = Depends(get_db)
):
    t = await db.get(Thought, thought_id)
    if not t:
        raise HTTPException(404, "thought not found")
    if not body.recipient_agent_ids:
        raise HTTPException(400, "at least one recipient agent is required")
    svc = DispatchService(db)
    dispatch = await svc.create_and_run(
        thought=t,
        recipient_agent_ids=body.recipient_agent_ids,
        default_mode=body.response_mode,
        per_agent_modes=body.per_agent_modes,
    )
    return {"dispatch_id": dispatch.id, "status": dispatch.status}


@router.get("/{thought_id}/detail")
async def thought_detail(thought_id: str, db: AsyncSession = Depends(get_db)):
    """Everything derived from a thought — full provenance (spec §23)."""
    t = await db.get(Thought, thought_id)
    if not t:
        raise HTTPException(404, "thought not found")
    dispatches = (
        await db.execute(
            select(AgentDispatch).where(AgentDispatch.thought_id == thought_id)
        )
    ).scalars().all()
    tasks = (
        await db.execute(select(Task).where(Task.originating_thought_id == thought_id))
    ).scalars().all()
    research = (
        await db.execute(
            select(ResearchJob).where(ResearchJob.originating_thought_id == thought_id)
        )
    ).scalars().all()
    memories = (
        await db.execute(select(Memory).where(Memory.originating_thought_id == thought_id))
    ).scalars().all()
    return {
        "thought": ThoughtOut.model_validate(t),
        "agent_dispatches": [
            {
                "id": d.id,
                "agent_id": d.agent_id,
                "status": d.status,
                "response_mode": d.response_mode,
                "response_summary": d.response_summary,
                "output": d.output,
            }
            for d in dispatches
        ],
        "tasks": [{"id": x.id, "title": x.title, "status": x.status} for x in tasks],
        "research_jobs": [{"id": x.id, "question": x.question, "status": x.status} for x in research],
        "memories": [
            {"id": x.id, "scope": x.scope, "category": x.category, "content": x.content}
            for x in memories
        ],
    }
