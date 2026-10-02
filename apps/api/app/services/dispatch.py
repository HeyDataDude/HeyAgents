"""Dispatch orchestration (spec §6, §9).

Creates a Dispatch + one AgentDispatch per recipient, then executes each agent independently so one
agent failing never blocks the others. QUICK/REMEMBER/TALK run inline; DEEP enqueues a durable job.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import (
    AgentDispatchStatus,
    DispatchStatus,
    ResponseMode,
    ThoughtStatus,
)
from app.core.logging import get_logger
from app.db.base import utcnow
from app.integrations.factory import get_providers
from app.models.agent import Agent
from app.models.dispatch import AgentDispatch, Dispatch
from app.models.thought import Thought
from app.services.activity import record_activity
from app.services.agents.apply import apply_agent_output
from app.services.agents.runner import AgentRunner

log = get_logger("council.dispatch")


class DispatchService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.providers = get_providers()
        self.runner = AgentRunner(self.providers.llm, mock=self.providers.settings.is_mock)

    async def create_and_run(
        self,
        *,
        thought: Thought,
        recipient_agent_ids: list[str],
        default_mode: ResponseMode,
        per_agent_modes: dict[str, ResponseMode] | None = None,
    ) -> Dispatch:
        per_agent_modes = per_agent_modes or {}
        dispatch = Dispatch(
            thought_id=thought.id,
            recipient_agent_ids=recipient_agent_ids,
            default_response_mode=default_mode.value,
            status=DispatchStatus.DISPATCHED.value,
        )
        self.db.add(dispatch)
        await self.db.flush()

        thought.status = ThoughtStatus.DISPATCHED.value

        agents = {
            a.id: a
            for a in (
                await self.db.execute(select(Agent).where(Agent.id.in_(recipient_agent_ids)))
            ).scalars()
        }

        completed = 0
        failed = 0
        for agent_id in recipient_agent_ids:
            agent = agents.get(agent_id)
            mode = per_agent_modes.get(agent_id, default_mode)
            ad = AgentDispatch(
                dispatch_id=dispatch.id,
                thought_id=thought.id,
                agent_id=agent_id,
                response_mode=mode.value,
                status=AgentDispatchStatus.QUEUED.value,
            )
            self.db.add(ad)
            await self.db.flush()

            if agent is None:
                ad.status = AgentDispatchStatus.FAILED.value
                ad.error = "agent not found"
                failed += 1
                continue

            if mode == ResponseMode.DEEP:
                # Durable path: enqueue, leave as processing. Worker completes it.
                ad.status = AgentDispatchStatus.PROCESSING.value
                ad.started_at = utcnow()
                await self._enqueue_deep(ad, agent, thought)
                continue

            # Inline path (QUICK / REMEMBER / TALK / AUTO).
            ad.status = AgentDispatchStatus.PROCESSING.value
            ad.started_at = utcnow()
            try:
                output = await self.runner.run(agent, thought, mode)
                if not output.relevant:
                    # The agent's lens genuinely doesn't apply — stay silent rather than add
                    # noise. No memory/task/connection side effects for a thought it rejected.
                    ad.output = output.model_dump(mode="json")
                    ad.response_summary = (
                        output.skip_reason or "Not relevant to this agent's lens."
                    )[:280]
                    ad.status = AgentDispatchStatus.SKIPPED.value
                    ad.completed_at = utcnow()
                    completed += 1
                    continue
                applied = await apply_agent_output(
                    self.db, agent=agent, thought=thought, output=output
                )
                ad.output = output.model_dump(mode="json")
                ad.response_summary = output.message[:280] or applied.summary
                ad.status = (
                    AgentDispatchStatus.WAITING_FOR_USER.value
                    if applied.question_ids
                    else AgentDispatchStatus.COMPLETED.value
                )
                ad.completed_at = utcnow()
                completed += 1
            except Exception as exc:  # one agent failing must not break others
                log.error("agent_dispatch_failed", agent=agent.slug, error=str(exc))
                ad.status = AgentDispatchStatus.FAILED.value
                ad.error = str(exc)
                failed += 1

        if failed and completed:
            dispatch.status = DispatchStatus.PARTIAL.value
        elif failed and not completed:
            dispatch.status = DispatchStatus.FAILED.value
        else:
            dispatch.status = DispatchStatus.COMPLETED.value

        await record_activity(
            self.db,
            kind="dispatch",
            message=(
                f"Dispatched “{thought.title}” to {len(recipient_agent_ids)} agent(s) "
                f"({completed} completed, {failed} failed)"
            ),
            links=[{"type": "thought", "id": thought.id, "label": thought.title}],
        )
        return dispatch

    async def _enqueue_deep(self, ad: AgentDispatch, agent: Agent, thought: Thought) -> None:
        from app.services.jobs import enqueue_job

        await enqueue_job(
            self.db,
            kind="deep_dispatch",
            payload={
                "agent_dispatch_id": ad.id,
                "agent_id": agent.id,
                "thought_id": thought.id,
                "mode": ad.response_mode,
            },
        )
