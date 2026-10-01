from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.job import Job
from app.services.intelligence import IntelligenceService
from app.services.jobs import enqueue_job

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.get("")
async def list_jobs(db: AsyncSession = Depends(get_db), status: str | None = None):
    stmt = select(Job).order_by(Job.created_at.desc()).limit(100)
    if status:
        stmt = stmt.where(Job.status == status)
    rows = (await db.execute(stmt)).scalars().all()
    return {
        "items": [
            {
                "id": j.id,
                "kind": j.kind,
                "status": j.status,
                "progress": j.progress,
                "attempts": j.attempts,
                "error": j.error,
                "created_at": j.created_at,
                "finished_at": j.finished_at,
            }
            for j in rows
        ]
    }


@router.post("/detect-connections")
async def detect_connections(db: AsyncSession = Depends(get_db)):
    """Run cross-agent intelligence synchronously (spec §17)."""
    found = await IntelligenceService(db).detect()
    return {"discovered": len(found)}


@router.post("/enqueue")
async def enqueue(kind: str, db: AsyncSession = Depends(get_db)):
    job = await enqueue_job(db, kind=kind, payload={})
    return {"id": job.id, "status": job.status}
