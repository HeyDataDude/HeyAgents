from __future__ import annotations

import pytest
from sqlalchemy import select

from app.core.enums import AutonomyLevel, MemoryScope
from app.models.task import Task
from app.models.thought import Thought
from app.schemas.agent_output import AgentOutput, MemoryUpdate, TaskProposal
from app.services.agents.apply import apply_agent_output


@pytest.mark.asyncio
async def test_observe_level_blocks_tasks(db, seeded):
    agent = await _agent(db, seeded, "documentary")  # OBSERVE level
    agent.autonomy_level = AutonomyLevel.OBSERVE.value
    thought = await _thought(db, seeded)
    out = AgentOutput(
        message="noted",
        tasks=[TaskProposal(title="should not be created")],
        memory_updates=[MemoryUpdate(scope=MemoryScope.AGENT, content="ok")],
    )
    result = await apply_agent_output(db, agent=agent, thought=thought, output=out)
    # OBSERVE: memory allowed, tasks blocked.
    assert result.memory_ids
    assert not result.task_ids
    tasks = (await db.execute(select(Task))).scalars().all()
    assert tasks == []


@pytest.mark.asyncio
async def test_recommend_creates_task_requiring_approval(db, seeded):
    agent = await _agent(db, seeded, "career")  # RECOMMEND level
    agent.autonomy_level = AutonomyLevel.RECOMMEND.value
    thought = await _thought(db, seeded)
    out = AgentOutput(tasks=[TaskProposal(title="draft outreach")])
    applied = await apply_agent_output(db, agent=agent, thought=thought, output=out)
    assert applied.task_ids
    task = (await db.execute(select(Task))).scalars().first()
    assert task.requires_user_approval is True
    assert task.approved is False


@pytest.mark.asyncio
async def test_create_internal_level_auto_approves(db, seeded):
    agent = await _agent(db, seeded, "builder")  # CREATE_INTERNAL level
    agent.autonomy_level = AutonomyLevel.CREATE_INTERNAL.value
    thought = await _thought(db, seeded)
    out = AgentOutput(tasks=[TaskProposal(title="scaffold repo")])
    result = await apply_agent_output(db, agent=agent, thought=thought, output=out)
    task = (await db.execute(select(Task))).scalars().first()
    assert task.approved is True
    assert task.requires_user_approval is False


async def _agent(db, seeded, slug):
    from app.models.agent import Agent

    return await db.get(Agent, seeded["agents"][slug])


async def _thought(db, seeded):
    t = Thought(user_id=seeded["user"].id, title="t", clean_transcript="x", raw_transcript="x")
    db.add(t)
    await db.flush()
    return t
