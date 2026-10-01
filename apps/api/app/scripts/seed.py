"""Seed demo data (spec §42).

Idempotent: safe to run on every boot. Creates the demo user, the eight specialist agents, and a
rich set of sample thoughts that are run through the REAL pipeline (refine + route + dispatch) so
the UI shows authentic, provenance-linked data on first launch — never a blank screen.
"""

from __future__ import annotations

import asyncio

from sqlalchemy import func, select

from app.core.config import get_settings
from app.core.enums import ResponseMode
from app.core.logging import configure_logging, get_logger
from app.db.session import SessionLocal
from app.models.agent import Agent
from app.models.user import User
from app.services.agents.definitions import SEED_AGENTS
from app.services.dispatch import DispatchService
from app.services.intake import IntakeService
from app.services.intelligence import IntelligenceService
from app.services.reports import ReportService

log = get_logger("council.seed")

SAMPLE_THOUGHTS = [
    (
        "I don't know, I was thinking today, why do some people just not shower? Like maybe "
        "depression is part of it, but maybe some people genuinely don't think about hygiene the "
        "same way. And maybe there's something broader there about things that seem obvious to one "
        "person but aren't obvious to another. Could be a content idea too."
    ),
    (
        "I keep coming back to this idea of building a personal system that captures my thinking so "
        "I don't lose ideas. Like a second brain but voice first. I should probably prototype the "
        "capture flow before anything else."
    ),
    (
        "I noticed I always start projects with huge energy and then stall around day three. Maybe "
        "there's a pattern where the novelty wears off and I don't have a system to carry me "
        "through. Not sure if that's motivation or just bad process."
    ),
    (
        "What if the way I explain technical things on video is actually my differentiator for my "
        "career, not just a hobby. Maybe I should treat content as portfolio, not a distraction."
    ),
    (
        "Random thought: the obvious-to-one-not-to-another idea connects to how I teach. The best "
        "explanations name the thing the expert forgot was ever confusing."
    ),
]


async def seed() -> None:
    configure_logging(get_settings().log_level)
    settings = get_settings()
    async with SessionLocal() as db:
        # Demo user
        user = (
            await db.execute(select(User).where(User.email == settings.demo_user_email))
        ).scalars().first()
        if not user:
            user = User(email=settings.demo_user_email, display_name="You")
            db.add(user)
            await db.flush()
            log.info("seeded_user", email=user.email)

        # Agents (idempotent by slug)
        existing_slugs = {
            a.slug for a in (await db.execute(select(Agent))).scalars().all()
        }
        slug_to_id: dict[str, str] = {}
        for defn in SEED_AGENTS:
            if defn.slug in existing_slugs:
                a = (
                    await db.execute(select(Agent).where(Agent.slug == defn.slug))
                ).scalars().first()
                slug_to_id[defn.slug] = a.id
                continue
            agent = Agent(
                name=defn.name,
                slug=defn.slug,
                description=defn.description,
                icon=defn.icon,
                accent=defn.accent,
                system_role=defn.system_role,
                routing_keywords=",".join(defn.routing_keywords),
                autonomy_level=defn.autonomy_level,
                interruption_policy=defn.interruption_policy,
                is_supervisor=defn.is_supervisor,
                provider=settings.llm_provider,
                model=settings.llm_default_model,
            )
            db.add(agent)
            await db.flush()
            slug_to_id[defn.slug] = agent.id
            log.info("seeded_agent", slug=agent.slug)

        await db.commit()

    # Only seed sample thoughts once (if there are none yet).
    async with SessionLocal() as db:
        from app.models.thought import Thought

        count = (await db.execute(select(func.count(Thought.id)))).scalar() or 0
        if count > 0:
            log.info("thoughts_exist_skip_sample", count=int(count))
            await _ensure_reports(db)
            await db.commit()
            return

        user = (
            await db.execute(select(User).where(User.email == settings.demo_user_email))
        ).scalars().first()
        intake = IntakeService(db)
        dispatch = DispatchService(db)

        for i, text in enumerate(SAMPLE_THOUGHTS):
            thought = await intake.capture_text(
                user_id=user.id, text=text, title=None, source="seed"
            )
            # Dispatch to the top suggested agents, varying the mode for realistic data.
            recipients = [s["agent_id"] for s in thought.routing_suggestions[:3]]
            if not recipients:
                recipients = [slug_to_id["research"]]
            mode = [ResponseMode.QUICK, ResponseMode.AUTO, ResponseMode.DEEP][i % 3]
            await dispatch.create_and_run(
                thought=thought,
                recipient_agent_ids=recipients,
                default_mode=mode,
            )
        await db.commit()

    async with SessionLocal() as db:
        # Cross-agent intelligence + reports so the dashboard is populated.
        await IntelligenceService(db).detect()
        await _ensure_reports(db)
        await db.commit()
        log.info("seed_complete")


async def _ensure_reports(db) -> None:
    from app.models.report import Report

    count = (await db.execute(select(func.count(Report.id)))).scalar() or 0
    if count:
        return
    svc = ReportService(db)
    await svc.generate_morning()
    await svc.generate_daily()
    await svc.generate_weekly()


if __name__ == "__main__":
    asyncio.run(seed())
