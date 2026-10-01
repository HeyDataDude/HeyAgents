"""Shared FastAPI dependencies: DB session, current user (single demo user for now).

Auth is intentionally pluggable. For the first version Council runs as a single-user system; the
`get_current_user` dependency is the single seam where real auth (JWT/OAuth/session) plugs in.
"""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.session import get_db
from app.models.user import User


async def get_current_user(db: AsyncSession = Depends(get_db)) -> User:
    settings = get_settings()
    user = (
        await db.execute(select(User).where(User.email == settings.demo_user_email))
    ).scalars().first()
    if user is None:
        # Lazily create the demo user so a fresh DB is never userless.
        user = User(email=settings.demo_user_email, display_name="You")
        db.add(user)
        await db.flush()
    return user
