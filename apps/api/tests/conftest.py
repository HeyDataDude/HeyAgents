"""Test fixtures.

Tests run against an in-memory SQLite database (aiosqlite) with provider mode = mock, so the whole
suite is offline and deterministic — no Postgres, Redis or API keys required.
"""

from __future__ import annotations

import os

os.environ.setdefault("COUNCIL_PROVIDER_MODE", "mock")
os.environ.setdefault("COUNCIL_DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("COUNCIL_STORAGE_BACKEND", "local")
os.environ.setdefault("COUNCIL_STORAGE_LOCAL_DIR", "/tmp/council-test-storage")

import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db.base import Base
from app.models import *  # noqa: F401,F403
from app.models.agent import Agent
from app.models.user import User
from app.services.agents.definitions import SEED_AGENTS


@pytest_asyncio.fixture
async def engine():
    eng = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture
async def db(engine):
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as session:
        yield session


@pytest_asyncio.fixture
async def seeded(db):
    user = User(email="test@example.com", display_name="Test")
    db.add(user)
    slug_to_id = {}
    for d in SEED_AGENTS:
        a = Agent(
            name=d.name, slug=d.slug, description=d.description, icon=d.icon, accent=d.accent,
            system_role=d.system_role, routing_keywords=",".join(d.routing_keywords),
            autonomy_level=d.autonomy_level, interruption_policy=d.interruption_policy,
            is_supervisor=d.is_supervisor,
        )
        db.add(a)
        await db.flush()
        slug_to_id[d.slug] = a.id
    await db.flush()
    return {"user": user, "agents": slug_to_id}
