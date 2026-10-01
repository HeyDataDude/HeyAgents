"""Durable background worker (spec §5, §16).

Processes jobs whose state lives in Postgres. Prefers a Redis BLPOP wake-up; falls back to DB
polling so jobs are never lost if Redis is down. Survives restarts: on boot it re-queues any job
left in QUEUED/WORKING.
"""

from __future__ import annotations

import asyncio

from sqlalchemy import select

from app.core.config import get_settings
from app.core.enums import (
    AgentDispatchStatus,
    JobStatus,
)
from app.core.logging import configure_logging, get_logger, job_id_ctx
from app.db.base import utcnow
from app.db.session import SessionLocal
from app.integrations.factory import get_providers
from app.models.agent import Agent
from app.models.dispatch import AgentDispatch
from app.models.job import Job
from app.models.research import ResearchJob
from app.models.thought import Thought
from app.services.agents.apply import apply_agent_output
from app.services.agents.runner import AgentRunner
from app.services.jobs import QUEUE_LIST
from app.services.research import ResearchExecutor

log = get_logger("council.worker")
settings = get_settings()


async def _claim_next_job(db) -> Job | None:
    job = (
        await db.execute(
            select(Job).where(Job.status == JobStatus.QUEUED.value).order_by(Job.created_at).limit(1)
        )
    ).scalars().first()
    if job:
        job.status = JobStatus.WORKING.value
        job.started_at = utcnow()
        job.attempts += 1
        await db.flush()
    return job


async def _process_job(db, job: Job) -> None:
    job_id_ctx.set(job.id)
    log.info("job_start", kind=job.kind)
    try:
        if job.kind == "deep_dispatch":
            await _handle_deep_dispatch(db, job)
        elif job.kind == "research":
            await _handle_research(db, job)
        elif job.kind == "daily_brief":
            from app.services.reports import ReportService

            report = await ReportService(db).generate_daily()
            job.result = {"report_id": report.id}
        elif job.kind == "detect_connections":
            from app.services.intelligence import IntelligenceService

            found = await IntelligenceService(db).detect()
            job.result = {"connections": len(found)}
        else:
            raise ValueError(f"unknown job kind: {job.kind}")
        job.status = JobStatus.COMPLETED.value
        job.progress = 100
    except Exception as exc:
        log.error("job_failed", error=str(exc))
        job.status = JobStatus.FAILED.value
        job.error = str(exc)
    finally:
        job.finished_at = utcnow()
        job_id_ctx.set(None)


async def _handle_deep_dispatch(db, job: Job) -> None:
    payload = job.payload
    ad = await db.get(AgentDispatch, payload["agent_dispatch_id"])
    agent = await db.get(Agent, payload["agent_id"])
    thought = await db.get(Thought, payload["thought_id"])
    if not (ad and agent and thought):
        raise ValueError("deep_dispatch: missing agent dispatch / agent / thought")

    providers = get_providers()
    runner = AgentRunner(providers.llm, mock=providers.settings.is_mock)
    from app.core.enums import ResponseMode

    output = await runner.run(agent, thought, ResponseMode.DEEP)
    applied = await apply_agent_output(db, agent=agent, thought=thought, output=output)
    ad.output = output.model_dump(mode="json")
    ad.response_summary = output.message[:280] or applied.summary
    ad.status = AgentDispatchStatus.COMPLETED.value
    ad.completed_at = utcnow()
    job.result = {"research_jobs": applied.research_ids, "tasks": applied.task_ids}

    # Chain: execute any research jobs the deep run produced.
    for rid in applied.research_ids:
        rj = await db.get(ResearchJob, rid)
        if rj:
            await ResearchExecutor(db).run(rj)


async def _handle_research(db, job: Job) -> None:
    rj = await db.get(ResearchJob, job.payload["research_job_id"])
    if not rj:
        raise ValueError("research: job not found")
    await ResearchExecutor(db).run(rj)
    job.result = {"status": rj.status}


async def _recover_orphans(db) -> None:
    """On boot, re-queue jobs stuck in WORKING (worker died mid-run)."""
    stuck = (
        await db.execute(select(Job).where(Job.status == JobStatus.WORKING.value))
    ).scalars().all()
    for job in stuck:
        job.status = JobStatus.QUEUED.value
    if stuck:
        log.info("recovered_orphan_jobs", count=len(stuck))


async def run_forever() -> None:
    configure_logging(settings.log_level)
    log.info("worker_boot", provider_mode=settings.provider_mode)

    async with SessionLocal() as db:
        await _recover_orphans(db)
        await db.commit()

    redis_client = None
    try:
        import redis.asyncio as redis

        redis_client = redis.from_url(settings.redis_url)
    except Exception as exc:
        log.warning("redis_unavailable_polling_only", error=str(exc))

    while True:
        processed = False
        async with SessionLocal() as db:
            try:
                job = await _claim_next_job(db)
                if job:
                    await _process_job(db, job)
                    processed = True
                await db.commit()
            except Exception as exc:
                await db.rollback()
                log.error("worker_loop_error", error=str(exc))

        if processed:
            continue  # drain quickly

        # Idle: wait for a Redis notification or poll after a short delay.
        if redis_client is not None:
            try:
                await redis_client.blpop(QUEUE_LIST, timeout=5)
                continue
            except Exception:
                pass
        await asyncio.sleep(2)


if __name__ == "__main__":
    asyncio.run(run_forever())
