"""Apply a validated AgentOutput to the database, enforcing autonomy levels (spec §11, §12).

Autonomy gate:
  LEVEL 0 OBSERVE                 -> memory + connections only; no tasks/research/questions.
  LEVEL 1 RECOMMEND               -> + questions_for_user; tasks created but require approval.
  LEVEL 2 CREATE_INTERNAL         -> + internal tasks/drafts/research without approval.
  LEVEL 3 EXTERNAL_WITH_APPROVAL  -> external actions allowed but each requires user approval.
  LEVEL 4 EXTERNAL_WHITELISTED    -> explicitly whitelisted external actions auto-run.

No external communication / purchasing / deletion / publishing happens autonomously here; those are
represented as approval-gated tasks regardless of level unless whitelisted.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import (
    AutonomyLevel,
    ConnectionType,
    MemoryScope,
    QuestionStatus,
    ResearchStatus,
)
from app.models.agent import Agent
from app.models.connection import Connection
from app.models.memory import Memory
from app.models.project import Project
from app.models.question import AgentQuestion
from app.models.research import ResearchJob
from app.models.task import Task
from app.models.thought import Thought
from app.schemas.agent_output import AgentOutput
from app.services.activity import record_activity


class AppliedResult:
    def __init__(self) -> None:
        self.task_ids: list[str] = []
        self.research_ids: list[str] = []
        self.memory_ids: list[str] = []
        self.question_ids: list[str] = []
        self.connection_ids: list[str] = []
        self.summary_parts: list[str] = []

    @property
    def summary(self) -> str:
        return "; ".join(self.summary_parts) or "no durable actions"


async def apply_agent_output(
    db: AsyncSession,
    *,
    agent: Agent,
    thought: Thought,
    output: AgentOutput,
) -> AppliedResult:
    level = agent.autonomy_level
    result = AppliedResult()

    # Memory updates — allowed at all levels (including OBSERVE).
    for mu in output.memory_updates:
        mem = Memory(
            scope=mu.scope.value,
            agent_id=agent.id if mu.scope == MemoryScope.AGENT else None,
            project_id=mu.project_id if mu.scope == MemoryScope.PROJECT else None,
            category=mu.category,
            content=mu.content,
            created_by_agent_id=agent.id,
            originating_thought_id=thought.id,
            provenance={"reason": "agent_output", "mode": "dispatch"},
        )
        db.add(mem)
        await db.flush()
        result.memory_ids.append(mem.id)
    if result.memory_ids:
        result.summary_parts.append(f"{len(result.memory_ids)} memory update(s)")

    # Connections — allowed at all levels; always provenance-stamped.
    for cp in output.connections:
        related = [{"type": "thought", "id": oid, "label": ""} for oid in cp.related_object_ids]
        if not related:
            related = [{"type": "thought", "id": thought.id, "label": thought.title}]
        cxn = Connection(
            type=cp.type.value if isinstance(cp.type, ConnectionType) else str(cp.type),
            title=cp.title,
            explanation=cp.explanation,
            confidence=cp.confidence,
            related_objects=related,
            discovered_by=agent.slug,
        )
        db.add(cxn)
        await db.flush()
        result.connection_ids.append(cxn.id)
    if result.connection_ids:
        result.summary_parts.append(f"{len(result.connection_ids)} connection(s)")

    # Questions for user — level >= RECOMMEND.
    if level >= AutonomyLevel.RECOMMEND.value:
        for q in output.questions_for_user:
            question = AgentQuestion(
                agent_id=agent.id,
                thought_id=thought.id,
                question=q.question,
                context=q.context,
                importance=q.importance.value,
                status=QuestionStatus.OPEN.value,
            )
            db.add(question)
            await db.flush()
            result.question_ids.append(question.id)
        if result.question_ids:
            result.summary_parts.append(f"{len(result.question_ids)} question(s)")

    # Tasks — created at level >= RECOMMEND; require approval unless level >= CREATE_INTERNAL.
    if level >= AutonomyLevel.RECOMMEND.value:
        for tp in output.tasks:
            requires_approval = tp.requires_user_approval or (
                level < AutonomyLevel.CREATE_INTERNAL.value
            )
            task = Task(
                title=tp.title,
                description=tp.description,
                created_by_agent_id=agent.id,
                originating_thought_id=thought.id,
                project_id=tp.project_id,
                priority=tp.priority.value,
                due_at=tp.due_at,
                requires_user_approval=requires_approval,
                approved=not requires_approval,
                rationale=tp.rationale,
            )
            db.add(task)
            await db.flush()
            result.task_ids.append(task.id)
        if result.task_ids:
            result.summary_parts.append(f"{len(result.task_ids)} task(s)")

    # Research jobs — queued at level >= CREATE_INTERNAL (deep internal work).
    if level >= AutonomyLevel.CREATE_INTERNAL.value or output.research_jobs:
        for rj in output.research_jobs:
            job = ResearchJob(
                question=rj.question,
                agent_id=agent.id,
                originating_thought_id=thought.id,
                status=ResearchStatus.QUEUED.value,
            )
            db.add(job)
            await db.flush()
            result.research_ids.append(job.id)
        if result.research_ids:
            result.summary_parts.append(f"{len(result.research_ids)} research job(s)")

    # Project updates — create/attach.
    for pu in output.project_updates:
        if pu.project_id is None and pu.name:
            project = Project(name=pu.name, description=pu.note, related_agent_ids=[agent.id],
                              related_thought_ids=[thought.id])
            db.add(project)
            await db.flush()

    await record_activity(
        db,
        kind="agent_run",
        actor=agent.slug,
        message=f"{agent.name} processed “{thought.title}” → {result.summary}",
        links=[{"type": "thought", "id": thought.id, "label": thought.title}],
    )
    return result
