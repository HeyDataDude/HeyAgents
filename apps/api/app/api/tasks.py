from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import Priority, TaskStatus
from app.db.session import get_db
from app.models.task import Task

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


class TaskCreate(BaseModel):
    title: str
    description: str = ""
    priority: Priority = Priority.MEDIUM
    project_id: str | None = None
    originating_thought_id: str | None = None


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: TaskStatus | None = None
    priority: Priority | None = None
    approved: bool | None = None


def _ser(t: Task) -> dict:
    return {
        "id": t.id,
        "title": t.title,
        "description": t.description,
        "status": t.status,
        "priority": t.priority,
        "created_by_agent_id": t.created_by_agent_id,
        "originating_thought_id": t.originating_thought_id,
        "project_id": t.project_id,
        "due_at": t.due_at,
        "requires_user_approval": t.requires_user_approval,
        "approved": t.approved,
        "rationale": t.rationale,
        "created_at": t.created_at,
    }


@router.get("")
async def list_tasks(
    db: AsyncSession = Depends(get_db),
    status: str | None = None,
    agent_id: str | None = None,
    project_id: str | None = None,
):
    stmt = select(Task).order_by(Task.created_at.desc())
    if status:
        stmt = stmt.where(Task.status == status)
    if agent_id:
        stmt = stmt.where(Task.created_by_agent_id == agent_id)
    if project_id:
        stmt = stmt.where(Task.project_id == project_id)
    rows = (await db.execute(stmt)).scalars().all()
    return {"items": [_ser(t) for t in rows]}


@router.post("", status_code=201)
async def create_task(body: TaskCreate, db: AsyncSession = Depends(get_db)):
    t = Task(
        title=body.title,
        description=body.description,
        priority=body.priority.value,
        project_id=body.project_id,
        originating_thought_id=body.originating_thought_id,
        approved=True,
    )
    db.add(t)
    await db.flush()
    return _ser(t)


@router.patch("/{task_id}")
async def update_task(task_id: str, body: TaskUpdate, db: AsyncSession = Depends(get_db)):
    t = await db.get(Task, task_id)
    if not t:
        raise HTTPException(404, "task not found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(t, k, v.value if hasattr(v, "value") else v)
    await db.flush()
    return _ser(t)


@router.delete("/{task_id}", status_code=204)
async def delete_task(task_id: str, db: AsyncSession = Depends(get_db)):
    t = await db.get(Task, task_id)
    if t:
        await db.delete(t)
    return None
