from __future__ import annotations

import pytest
from sqlalchemy import select

from app.core.enums import JobStatus, ResponseMode
from app.models.job import Job
from app.services.dispatch import DispatchService
from app.services.intake import IntakeService
from app.services.reports import ReportService


@pytest.mark.asyncio
async def test_daily_report_generation_from_real_state(db, seeded):
    intake = IntakeService(db)
    t = await intake.capture_text(
        user_id=seeded["user"].id, text="I want to build a voice second brain app.", title=None, source="t"
    )
    await DispatchService(db).create_and_run(
        thought=t,
        recipient_agent_ids=[t.routing_suggestions[0]["agent_id"]],
        default_mode=ResponseMode.AUTO,
    )
    report = await ReportService(db).generate_daily()
    assert report.content["headline"]["thoughts_captured"] >= 1
    assert "needs_you" in report.content


@pytest.mark.asyncio
async def test_deep_mode_enqueues_durable_job(db, seeded):
    intake = IntakeService(db)
    t = await intake.capture_text(
        user_id=seeded["user"].id, text="Why does sleep timing matter for focus?", title=None, source="t"
    )
    await DispatchService(db).create_and_run(
        thought=t,
        recipient_agent_ids=[t.routing_suggestions[0]["agent_id"]],
        default_mode=ResponseMode.DEEP,
    )
    jobs = (await db.execute(select(Job).where(Job.kind == "deep_dispatch"))).scalars().all()
    assert jobs
    assert jobs[0].status == JobStatus.QUEUED.value
