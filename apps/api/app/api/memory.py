from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import MemoryScope
from app.db.session import get_db
from app.models.agent import Agent
from app.models.memory import Memory

router = APIRouter(prefix="/api/memory", tags=["memory"])


class MemoryCreate(BaseModel):
    scope: MemoryScope = MemoryScope.GLOBAL
    category: str = "General"
    content: str
    agent_id: str | None = None
    project_id: str | None = None


class MemoryUpdateBody(BaseModel):
    category: str | None = None
    content: str | None = None


def _ser(m: Memory) -> dict:
    return {
        "id": m.id,
        "scope": m.scope,
        "category": m.category,
        "content": m.content,
        "agent_id": m.agent_id,
        "project_id": m.project_id,
        "created_by_agent_id": m.created_by_agent_id,
        "originating_thought_id": m.originating_thought_id,
        "provenance": m.provenance,
        "created_at": m.created_at,
    }


@router.get("")
async def list_memory(
    db: AsyncSession = Depends(get_db),
    scope: str | None = None,
    agent_id: str | None = None,
    q: str | None = None,
):
    stmt = select(Memory).order_by(Memory.created_at.desc())
    if scope:
        stmt = stmt.where(Memory.scope == scope)
    if agent_id:
        stmt = stmt.where(Memory.agent_id == agent_id)
    if q:
        stmt = stmt.where(Memory.content.ilike(f"%{q}%"))
    rows = (await db.execute(stmt)).scalars().all()
    return {"items": [_ser(m) for m in rows]}


@router.get("/tree")
async def memory_tree(db: AsyncSession = Depends(get_db)):
    """Top-level GLOBAL / AGENTS / PROJECTS structure for the Memory Explorer (spec §31)."""
    all_mem = (await db.execute(select(Memory))).scalars().all()
    agents = {a.id: a.name for a in (await db.execute(select(Agent))).scalars()}

    global_cats: dict[str, int] = {}
    agent_counts: dict[str, int] = {}
    project_counts: dict[str, int] = {}
    for m in all_mem:
        if m.scope == MemoryScope.GLOBAL.value:
            global_cats[m.category] = global_cats.get(m.category, 0) + 1
        elif m.scope == MemoryScope.AGENT.value and m.agent_id:
            agent_counts[m.agent_id] = agent_counts.get(m.agent_id, 0) + 1
        elif m.scope == MemoryScope.PROJECT.value and m.project_id:
            project_counts[m.project_id] = project_counts.get(m.project_id, 0) + 1

    return {
        "global": [{"category": c, "count": n} for c, n in sorted(global_cats.items())],
        "agents": [
            {"agent_id": aid, "agent_name": agents.get(aid, aid), "count": n}
            for aid, n in agent_counts.items()
        ],
        "projects": [{"project_id": pid, "count": n} for pid, n in project_counts.items()],
    }


@router.post("", status_code=201)
async def create_memory(body: MemoryCreate, db: AsyncSession = Depends(get_db)):
    m = Memory(
        scope=body.scope.value,
        category=body.category,
        content=body.content,
        agent_id=body.agent_id,
        project_id=body.project_id,
        provenance={"reason": "user_created"},
    )
    db.add(m)
    await db.flush()
    return _ser(m)


@router.patch("/{memory_id}")
async def update_memory(memory_id: str, body: MemoryUpdateBody, db: AsyncSession = Depends(get_db)):
    m = await db.get(Memory, memory_id)
    if not m:
        raise HTTPException(404, "memory not found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(m, k, v)
    await db.flush()
    return _ser(m)


@router.delete("/{memory_id}", status_code=204)
async def delete_memory(memory_id: str, db: AsyncSession = Depends(get_db)):
    m = await db.get(Memory, memory_id)
    if m:
        await db.delete(m)
    return None
