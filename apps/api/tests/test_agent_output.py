from __future__ import annotations

import pytest

from app.schemas.agent_output import AgentOutput


def test_agent_output_parses_minimal():
    out = AgentOutput.model_validate({"message": "hi"})
    assert out.message == "hi"
    assert out.tasks == []
    assert out.notification_request is None


def test_agent_output_parses_full_contract():
    data = {
        "message": "Analysis",
        "memory_updates": [{"scope": "agent", "category": "Notes", "content": "x"}],
        "tasks": [{"title": "Do thing", "priority": "high", "requires_user_approval": True}],
        "research_jobs": [{"question": "why?"}],
        "questions_for_user": [{"question": "which scope?", "importance": "needs_decision"}],
        "connections": [{"title": "theme", "explanation": "e", "confidence": 0.6}],
        "artifacts": [{"name": "draft", "content": "md"}],
    }
    out = AgentOutput.model_validate(data)
    assert out.tasks[0].requires_user_approval is True
    assert out.research_jobs[0].question == "why?"
    assert out.connections[0].confidence == 0.6


def test_agent_output_rejects_bad_types():
    with pytest.raises(Exception):
        AgentOutput.model_validate({"tasks": "not-a-list"})
