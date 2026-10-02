"""End-to-end test (spec §47): create thought -> refine -> route -> dispatch -> agent response
-> task/memory creation -> all visible/traceable."""

from __future__ import annotations

import pytest
from sqlalchemy import select

from app.core.enums import AgentDispatchStatus, ResponseMode, ThoughtStatus
from app.models.dispatch import AgentDispatch
from app.models.memory import Memory
from app.services.dispatch import DispatchService
from app.services.intake import IntakeService

RAW = (
    "I was thinking why do some people not shower, maybe depression, maybe hygiene just isn't "
    "salient to them. Could be a content idea too."
)


@pytest.mark.asyncio
async def test_full_voice_thought_loop(db, seeded):
    intake = IntakeService(db)
    thought = await intake.capture_text(user_id=seeded["user"].id, text=RAW, title=None, source="test")

    # Refined + structured + routed.
    assert thought.status == ThoughtStatus.READY_FOR_REVIEW.value
    assert thought.clean_transcript
    assert thought.topics
    assert thought.routing_suggestions

    recipients = [s["agent_id"] for s in thought.routing_suggestions[:3]]
    assert recipients

    dispatch = DispatchService(db)
    d = await dispatch.create_and_run(
        thought=thought, recipient_agent_ids=recipients, default_mode=ResponseMode.AUTO
    )

    assert thought.status == ThoughtStatus.DISPATCHED.value

    # One AgentDispatch per recipient.
    rows = (
        await db.execute(select(AgentDispatch).where(AgentDispatch.thought_id == thought.id))
    ).scalars().all()
    assert len(rows) == len(recipients)
    terminal = {
        AgentDispatchStatus.COMPLETED.value,
        AgentDispatchStatus.WAITING_FOR_USER.value,
        AgentDispatchStatus.SKIPPED.value,  # agent's lens may genuinely not apply
        AgentDispatchStatus.PROCESSING.value,  # deep mode may still be processing
    }
    assert all(r.status in terminal for r in rows)

    # Memories created and traceable back to the originating thought.
    memories = (
        await db.execute(select(Memory).where(Memory.originating_thought_id == thought.id))
    ).scalars().all()
    assert memories
    assert all(m.originating_thought_id == thought.id for m in memories)


@pytest.mark.asyncio
async def test_one_agent_failure_does_not_block_others(db, seeded):
    intake = IntakeService(db)
    thought = await intake.capture_text(user_id=seeded["user"].id, text=RAW, title=None, source="test")
    dispatch = DispatchService(db)
    # Include a bogus agent id — it should fail in isolation.
    good = thought.routing_suggestions[0]["agent_id"]
    dispatch_row = await dispatch.create_and_run(
        thought=thought,
        recipient_agent_ids=[good, "agt_doesnotexist"],
        default_mode=ResponseMode.QUICK,
    )
    rows = (
        await db.execute(select(AgentDispatch).where(AgentDispatch.thought_id == thought.id))
    ).scalars().all()
    statuses = {r.agent_id: r.status for r in rows}
    assert statuses["agt_doesnotexist"] == AgentDispatchStatus.FAILED.value
    assert statuses[good] in (
        AgentDispatchStatus.COMPLETED.value,
        AgentDispatchStatus.WAITING_FOR_USER.value,
    )
    # Dispatch should be PARTIAL (some ok, one failed).
    assert dispatch_row.status == "partial"
