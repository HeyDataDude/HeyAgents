from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.activity import Activity
from app.models.connection import Connection

router = APIRouter(prefix="/api/activity", tags=["activity"])


@router.get("")
async def list_activity(db: AsyncSession = Depends(get_db), limit: int = Query(80, le=300)):
    rows = (
        await db.execute(select(Activity).order_by(Activity.created_at.desc()).limit(limit))
    ).scalars().all()
    return {
        "items": [
            {
                "id": a.id,
                "kind": a.kind,
                "message": a.message,
                "actor": a.actor,
                "links": a.links,
                "level": a.level,
                "created_at": a.created_at,
            }
            for a in rows
        ]
    }


@router.get("/connections")
async def list_connections(db: AsyncSession = Depends(get_db)):
    rows = (
        await db.execute(
            select(Connection).where(Connection.dismissed.is_(False)).order_by(
                Connection.confidence.desc()
            )
        )
    ).scalars().all()
    return {
        "items": [
            {
                "id": c.id,
                "type": c.type,
                "title": c.title,
                "explanation": c.explanation,
                "confidence": c.confidence,
                "related_objects": c.related_objects,
                "discovered_by": c.discovered_by,
                "created_at": c.created_at,
            }
            for c in rows
        ]
    }
