from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import MessageRole
from app.db.session import get_db
from app.integrations.base import LLMMessage
from app.integrations.factory import get_providers
from app.models.agent import Agent
from app.models.conversation import Conversation, Message

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


class StartConversation(BaseModel):
    agent_id: str
    title: str | None = None


class SendMessage(BaseModel):
    content: str


def _ser_msg(m: Message) -> dict:
    return {
        "id": m.id,
        "role": m.role,
        "agent_id": m.agent_id,
        "content": m.content,
        "created_at": m.created_at,
    }


@router.get("")
async def list_conversations(db: AsyncSession = Depends(get_db), agent_id: str | None = None):
    stmt = select(Conversation).order_by(Conversation.updated_at.desc())
    if agent_id:
        stmt = stmt.where(Conversation.agent_id == agent_id)
    rows = (await db.execute(stmt)).scalars().all()
    return {
        "items": [
            {"id": c.id, "title": c.title, "agent_id": c.agent_id, "mode": c.mode, "is_council": c.is_council}
            for c in rows
        ]
    }


@router.post("", status_code=201)
async def start_conversation(body: StartConversation, db: AsyncSession = Depends(get_db)):
    agent = await db.get(Agent, body.agent_id)
    if not agent:
        raise HTTPException(404, "agent not found")
    conv = Conversation(title=body.title or f"Chat: {agent.name}", agent_id=agent.id, mode="text")
    db.add(conv)
    await db.flush()
    return {"id": conv.id, "title": conv.title, "agent_id": conv.agent_id}


@router.get("/{conversation_id}/messages")
async def get_messages(conversation_id: str, db: AsyncSession = Depends(get_db)):
    rows = (
        await db.execute(
            select(Message).where(Message.conversation_id == conversation_id).order_by(Message.created_at)
        )
    ).scalars().all()
    return {"items": [_ser_msg(m) for m in rows]}


@router.post("/{conversation_id}/messages")
async def send_message(conversation_id: str, body: SendMessage, db: AsyncSession = Depends(get_db)):
    conv = await db.get(Conversation, conversation_id)
    if not conv:
        raise HTTPException(404, "conversation not found")
    user_msg = Message(conversation_id=conv.id, role=MessageRole.USER.value, content=body.content)
    db.add(user_msg)
    await db.flush()

    providers = get_providers()
    agent = await db.get(Agent, conv.agent_id) if conv.agent_id else None
    system = agent.system_role if agent else "You are a helpful specialist."
    reply = await providers.llm.complete(
        [LLMMessage("system", system), LLMMessage("user", body.content)]
    )
    agent_msg = Message(
        conversation_id=conv.id,
        role=MessageRole.AGENT.value,
        agent_id=conv.agent_id,
        content=reply,
    )
    db.add(agent_msg)
    await db.flush()
    return {"user_message": _ser_msg(user_msg), "agent_message": _ser_msg(agent_msg)}
