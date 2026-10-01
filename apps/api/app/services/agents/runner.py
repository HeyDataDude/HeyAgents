"""Agent runner — executes one agent against one thought and returns a validated AgentOutput.

Response modes (spec §9) shape what the agent produces:
  TALK      -> conversational opener (short), no durable work
  QUICK     -> concise analysis, maybe a memory note
  DEEP      -> queues a durable research/reasoning job + analysis
  REMEMBER  -> memory updates only, no user-facing message required
  AUTO      -> the agent chooses an appropriate combination

In mock mode each agent has a tailored, deterministic generator so outputs look specialist-specific.
In live mode the agent calls its persistent (Letta) agent + LLM and the JSON is validated against
the AgentOutput schema. Invalid/destructive actions are filtered by autonomy downstream.
"""

from __future__ import annotations

from app.core.enums import (
    ConnectionType,
    InterruptionPolicy,
    MemoryScope,
    Priority,
    ResponseMode,
)
from app.integrations.base import LLMMessage, LLMProvider
from app.models.agent import Agent
from app.models.thought import Thought
from app.schemas.agent_output import (
    AgentOutput,
    ConnectionProposal,
    MemoryUpdate,
    QuestionForUser,
    ResearchJobProposal,
    TaskProposal,
)


class AgentRunner:
    def __init__(self, llm: LLMProvider, *, mock: bool):
        self._llm = llm
        self._mock = mock

    async def run(self, agent: Agent, thought: Thought, mode: ResponseMode) -> AgentOutput:
        if self._mock:
            return self._run_mock(agent, thought, mode)
        return await self._run_llm(agent, thought, mode)

    async def _run_llm(self, agent: Agent, thought: Thought, mode: ResponseMode) -> AgentOutput:
        system = (
            f"{agent.system_role}\n\nReturn STRICT JSON matching the AgentOutput schema with keys: "
            "message, memory_updates, tasks, research_jobs, project_updates, questions_for_user, "
            "connections, artifacts, notification_request. Response mode: " + mode.value
        )
        messages = [
            LLMMessage("system", system),
            LLMMessage(
                "user",
                f"Thought title: {thought.title}\nClean thought: {thought.clean_transcript}\n"
                f"Topics: {thought.topics}\nQuestions: {thought.questions}\n"
                f"Possible actions: {thought.possible_actions}\n\nRespond as JSON.",
            ),
        ]
        try:
            data = await self._llm.complete_json(messages)
            return AgentOutput.model_validate(data)
        except Exception:
            # Robust: a bad agent response must not crash the dispatch.
            return self._run_mock(agent, thought, mode)

    # ── Mock specialist generators ────────────────────────────────────────────
    def _run_mock(self, agent: Agent, thought: Thought, mode: ResponseMode) -> AgentOutput:
        gen = _GENERATORS.get(agent.slug, _generic)
        out = gen(agent, thought)
        return self._apply_mode(out, agent, thought, mode)

    def _apply_mode(
        self, out: AgentOutput, agent: Agent, thought: Thought, mode: ResponseMode
    ) -> AgentOutput:
        if mode == ResponseMode.REMEMBER:
            # Memory only, no user-facing message.
            return AgentOutput(
                message="",
                memory_updates=out.memory_updates
                or [
                    MemoryUpdate(
                        scope=MemoryScope.AGENT,
                        category="Observations",
                        content=f"Noted thought '{thought.title}'.",
                    )
                ],
            )
        if mode == ResponseMode.TALK:
            return AgentOutput(message=out.message or f"Let's talk about {thought.title}.")
        if mode == ResponseMode.QUICK:
            # Keep durable side effects minimal for quick mode.
            return AgentOutput(
                message=out.message,
                memory_updates=out.memory_updates[:1],
                questions_for_user=out.questions_for_user[:1],
                connections=out.connections[:1],
            )
        if mode == ResponseMode.DEEP:
            # Ensure a research job exists for deep mode.
            research = out.research_jobs or [
                ResearchJobProposal(
                    question=(thought.questions[0] if thought.questions else thought.title),
                    rationale=f"Deep analysis requested from {agent.name}.",
                )
            ]
            out.research_jobs = research
            return out
        # AUTO — the agent's full chosen combination.
        return out


# ── per-agent generators (deterministic, specialist-flavored) ─────────────────────
def _generic(agent: Agent, t: Thought) -> AgentOutput:
    return AgentOutput(
        message=f"{agent.name} reviewed “{t.title}”. {t.summary}",
        memory_updates=[
            MemoryUpdate(scope=MemoryScope.AGENT, category="Notes", content=t.summary or t.title)
        ],
    )


def _research(agent: Agent, t: Thought) -> AgentOutput:
    q = t.questions[0] if t.questions else f"What explains: {t.title}?"
    return AgentOutput(
        message=(
            f"Good question to investigate: “{q}”. I'll separate what's actually evidenced from "
            "what's speculation. Early framing: there are likely multiple contributing factors, and "
            "I'm treating the depression link as a hypothesis, not a conclusion."
        ),
        research_jobs=[ResearchJobProposal(question=q, rationale="Core open question in the thought.")],
        memory_updates=[
            MemoryUpdate(
                scope=MemoryScope.AGENT,
                category="Open questions",
                content=f"Investigating: {q}",
            )
        ],
        questions_for_user=[
            QuestionForUser(
                question="Do you want sources focused on behavioral psychology or on public-health data?",
                context=f"Scoping the research for: {t.title}",
                importance=InterruptionPolicy.NEEDS_DECISION,
            )
        ],
    )


def _content(agent: Agent, t: Thought) -> AgentOutput:
    return AgentOutput(
        message=(
            f"There's a strong content angle here. Hook idea: “{t.title} — and what it reveals about "
            "the things we assume everyone sees the way we do.” Format could be a short essay or a "
            "talking-head video that leads with the uncomfortable question."
        ),
        tasks=[
            TaskProposal(
                title=f"Draft content outline: {t.title}",
                description="Lead with the hook; keep the user's exploratory voice; end on the "
                "'obvious to one, invisible to another' theme.",
                priority=Priority.MEDIUM,
                rationale="Thought was flagged as a possible content idea.",
            )
        ],
        memory_updates=[
            MemoryUpdate(scope=MemoryScope.AGENT, category="Content ideas", content=t.title)
        ],
    )


def _documentary(agent: Agent, t: Thought) -> AgentOutput:
    # Deliberately restrained — not every thought is documentary-worthy.
    return AgentOutput(
        message="",
        memory_updates=[
            MemoryUpdate(
                scope=MemoryScope.AGENT,
                category="Timeline",
                content=f"{t.created_at:%Y-%m-%d}: reflected on perception gaps ('{t.title}').",
            )
        ],
        connections=[
            ConnectionProposal(
                type=ConnectionType.SHARED_THEME,
                title="Recurring theme: what's obvious to one isn't to another",
                explanation="This echoes earlier reflections about perspective and assumptions.",
                confidence=0.55,
                related_object_ids=[t.id],
            )
        ],
    )


def _behavior(agent: Agent, t: Thought) -> AgentOutput:
    return AgentOutput(
        message=(
            "Carefully: this touches on how routines and perceived salience differ between people. "
            "I won't diagnose anything. One cautious experiment: note when a 'default' behavior is "
            "driven by low salience vs. low capacity — they look similar but respond to different "
            "interventions."
        ),
        memory_updates=[
            MemoryUpdate(
                scope=MemoryScope.AGENT,
                category="Patterns",
                content="User is interested in salience vs. capacity as distinct behavioral drivers.",
            )
        ],
    )


def _builder(agent: Agent, t: Thought) -> AgentOutput:
    return AgentOutput(
        message=f"If “{t.title}” becomes a build, I'd scope a tiny MVP first and expand.",
        tasks=[
            TaskProposal(
                title=f"Define MVP scope for: {t.title}",
                description="One sentence problem, 3 must-haves, explicit non-goals.",
                priority=Priority.LOW,
                rationale="Converting an idea into a concrete, bounded build.",
            )
        ],
    )


_GENERATORS = {
    "research": _research,
    "content": _content,
    "documentary": _documentary,
    "behavior": _behavior,
    "builder": _builder,
}
