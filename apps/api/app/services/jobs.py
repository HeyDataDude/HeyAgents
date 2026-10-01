"""Durable job queue (spec §16).

Job state lives in Postgres (survives restarts); Redis is used as a fast notification channel so the
worker wakes promptly. If Redis is unavailable the worker falls back to DB polling, so jobs are
never lost — they just run a little later.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.job import Job

log = get_logger("council.jobs")
QUEUE_CHANNEL = "council:jobs"
QUEUE_LIST = "council:jobs:pending"


async def enqueue_job(db: AsyncSession, *, kind: str, payload: dict) -> Job:
    job = Job(kind=kind, payload=payload)
    db.add(job)
    await db.flush()
    await _notify(job.id)
    return job


async def _notify(job_id: str) -> None:
    try:
        import redis.asyncio as redis

        client = redis.from_url(get_settings().redis_url)
        await client.rpush(QUEUE_LIST, job_id)
        await client.publish(QUEUE_CHANNEL, job_id)
        await client.aclose()
    except Exception as exc:  # non-fatal: worker will pick it up via DB polling
        log.warning("job_notify_failed", error=str(exc))
