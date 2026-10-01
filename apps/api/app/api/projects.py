from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.project import Project
from app.models.research import ResearchJob
from app.models.task import Task
from app.models.thought import Thought

router = APIRouter(prefix="/api/projects", tags=["projects"])


class ProjectCreate(BaseModel):
    name: str
    description: str = ""
    goals: list[str] = []


def _ser(p: Project) -> dict:
    return {
        "id": p.id,
        "name": p.name,
        "description": p.description,
        "status": p.status,
        "goals": p.goals,
        "related_agent_ids": p.related_agent_ids,
        "related_thought_ids": p.related_thought_ids,
        "related_task_ids": p.related_task_ids,
        "created_at": p.created_at,
    }


@router.get("")
async def list_projects(db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(Project).order_by(Project.created_at.desc()))).scalars().all()
    return {"items": [_ser(p) for p in rows]}


@router.post("", status_code=201)
async def create_project(body: ProjectCreate, db: AsyncSession = Depends(get_db)):
    p = Project(name=body.name, description=body.description, goals=body.goals)
    db.add(p)
    await db.flush()
    return _ser(p)


@router.get("/{project_id}")
async def get_project(project_id: str, db: AsyncSession = Depends(get_db)):
    p = await db.get(Project, project_id)
    if not p:
        raise HTTPException(404, "project not found")
    tasks = (await db.execute(select(Task).where(Task.project_id == project_id))).scalars().all()
    research = (
        await db.execute(select(ResearchJob).where(ResearchJob.agent_id.is_not(None)))
    ).scalars().all()
    thoughts = []
    if p.related_thought_ids:
        thoughts = (
            await db.execute(select(Thought).where(Thought.id.in_(p.related_thought_ids)))
        ).scalars().all()
    return {
        "project": _ser(p),
        "tasks": [{"id": t.id, "title": t.title, "status": t.status} for t in tasks],
        "thoughts": [{"id": t.id, "title": t.title} for t in thoughts],
        "research_jobs": [
            {"id": r.id, "question": r.question, "status": r.status}
            for r in research
            if r.originating_thought_id in (p.related_thought_ids or [])
        ],
    }
