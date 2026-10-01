from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.research import ResearchJob
from app.services.jobs import enqueue_job

router = APIRouter(prefix="/api/research", tags=["research"])


class ResearchCreate(BaseModel):
    question: str
    agent_id: str | None = None
    originating_thought_id: str | None = None


def _ser(r: ResearchJob) -> dict:
    return {
        "id": r.id,
        "question": r.question,
        "agent_id": r.agent_id,
        "originating_thought_id": r.originating_thought_id,
        "status": r.status,
        "progress": r.progress,
        "sources": r.sources,
        "findings": r.findings,
        "artifact_uri": r.artifact_uri,
        "error": r.error,
        "created_at": r.created_at,
    }


@router.get("")
async def list_research(db: AsyncSession = Depends(get_db), status: str | None = None):
    stmt = select(ResearchJob).order_by(ResearchJob.created_at.desc())
    if status:
        stmt = stmt.where(ResearchJob.status == status)
    rows = (await db.execute(stmt)).scalars().all()
    return {"items": [_ser(r) for r in rows]}


@router.get("/{research_id}")
async def get_research(research_id: str, db: AsyncSession = Depends(get_db)):
    r = await db.get(ResearchJob, research_id)
    if not r:
        raise HTTPException(404, "research job not found")
    return _ser(r)


@router.post("", status_code=201)
async def create_research(body: ResearchCreate, db: AsyncSession = Depends(get_db)):
    r = ResearchJob(
        question=body.question,
        agent_id=body.agent_id,
        originating_thought_id=body.originating_thought_id,
    )
    db.add(r)
    await db.flush()
    await enqueue_job(db, kind="research", payload={"research_job_id": r.id})
    return _ser(r)
