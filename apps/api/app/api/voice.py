from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.integrations.factory import get_providers
from app.models.agent import Agent
from app.models.conversation import Conversation

router = APIRouter(prefix="/api/voice", tags=["voice"])


class RealtimeTokenRequest(BaseModel):
    agent_id: str
    identity: str = "user"


class CouncilCallRequest(BaseModel):
    participant_agent_ids: list[str]
    identity: str = "user"


@router.post("/session")
async def create_realtime_session(body: RealtimeTokenRequest, db: AsyncSession = Depends(get_db)):
    """Mint a realtime voice session (spec §14). Mock provider returns a usable fake token."""
    agent = await db.get(Agent, body.agent_id)
    if not agent:
        raise HTTPException(404, "agent not found")
    providers = get_providers()
    room = f"talk-{agent.slug}"
    session = await providers.realtime.create_session(identity=body.identity, room=room)
    conv = Conversation(title=f"Voice: {agent.name}", agent_id=agent.id, mode="voice")
    db.add(conv)
    await db.flush()
    return {
        "conversation_id": conv.id,
        "provider": session.provider,
        "room": session.room,
        "token": session.token,
        "url": session.url,
        "agent": {"id": agent.id, "name": agent.name, "slug": agent.slug},
    }


@router.post("/council-call")
async def create_council_call(body: CouncilCallRequest, db: AsyncSession = Depends(get_db)):
    """Multi-agent voice session with a moderator (spec §15)."""
    agents = (
        await db.execute(select(Agent).where(Agent.id.in_(body.participant_agent_ids)))
    ).scalars().all()
    if not agents:
        raise HTTPException(400, "no valid participants")
    providers = get_providers()
    session = await providers.realtime.create_session(identity=body.identity, room="council-call")
    conv = Conversation(
        title="Council Call",
        is_council=True,
        participant_agent_ids=[a.id for a in agents],
        mode="voice",
    )
    db.add(conv)
    await db.flush()
    return {
        "conversation_id": conv.id,
        "provider": session.provider,
        "room": session.room,
        "token": session.token,
        "url": session.url,
        "participants": [{"id": a.id, "name": a.name, "slug": a.slug} for a in agents],
        "moderator": "Chief of Staff",
    }
