from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.session import get_db
from app.integrations.factory import get_providers
from app.models.agent import Agent
from app.models.job import Job
from app.models.thought import Thought

router = APIRouter(tags=["system"])


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.get("/api/system/diagnostics")
async def diagnostics(db: AsyncSession = Depends(get_db)):
    """Developer/admin diagnostics (spec §35)."""
    settings = get_settings()
    providers = get_providers()

    db_ok = True
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        db_ok = False

    redis_ok = False
    try:
        import redis.asyncio as redis

        client = redis.from_url(settings.redis_url)
        redis_ok = await client.ping()
        await client.aclose()
    except Exception:
        redis_ok = False

    thought_count = (await db.execute(select(func.count(Thought.id)))).scalar() or 0
    agent_count = (await db.execute(select(func.count(Agent.id)))).scalar() or 0
    pending_jobs = (
        await db.execute(select(func.count(Job.id)).where(Job.status == "queued"))
    ).scalar() or 0

    return {
        "env": settings.env,
        "provider_mode": settings.provider_mode,
        "providers": providers.health(),
        "database": {"ok": db_ok, "thoughts": int(thought_count), "agents": int(agent_count)},
        "redis": {"ok": bool(redis_ok)},
        "queue": {"pending_jobs": int(pending_jobs)},
        "storage_backend": settings.storage_backend,
    }
