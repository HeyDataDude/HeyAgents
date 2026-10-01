"""Activity feed service — records human-readable, link-rich events (spec §34)."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.activity import Activity


async def record_activity(
    db: AsyncSession,
    *,
    kind: str,
    message: str,
    actor: str = "system",
    links: list[dict] | None = None,
    level: str = "info",
) -> Activity:
    activity = Activity(
        kind=kind, message=message, actor=actor, links=links or [], level=level
    )
    db.add(activity)
    await db.flush()
    return activity
