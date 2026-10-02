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
        if not out.relevant:
            # A rejection is final — no response-mode reshaping should resurrect a message or
            # side effects out of an agent that decided this thought isn't in its lens.
            return out
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
def _text(t: Thought) -> str:
    return " ".join(
        [t.clean_transcript or "", " ".join(t.topics), " ".join(t.possible_actions), " ".join(t.questions)]
    ).lower()


def _any(text: str, keywords: tuple[str, ...]) -> str | None:
    return next((k for k in keywords if k in text), None)


def _generic(agent: Agent, t: Thought) -> AgentOutput:
    # Fallback for any agent without a dedicated generator — still applies the same lens
    # discipline via its own routing_keywords rather than always responding.
    text = _text(t)
    keywords = tuple(k.strip() for k in agent.routing_keywords.split(",") if k.strip())
    hit = _any(text, keywords) if keywords else None
    if keywords and not hit:
        return AgentOutput(
            relevant=False,
            skip_reason=f"Nothing in this thought falls inside {agent.name}'s lens.",
        )
    return AgentOutput(
        message=f"{agent.name} reviewed “{t.title}”. {t.summary}",
        memory_updates=[
            MemoryUpdate(scope=MemoryScope.AGENT, category="Notes", content=t.summary or t.title)
        ],
    )


def _research(agent: Agent, t: Thought) -> AgentOutput:
    text = _text(t)
    has_question = bool(t.questions)
    hit = _any(text, ("why", "how", "research", "evidence", "study", "cause", "investigate", "science"))
    if not has_question and not hit:
        return AgentOutput(
            relevant=False,
            skip_reason="No open question or evidence-worthy claim here to investigate.",
        )
    q = t.questions[0] if t.questions else f"What's actually going on with: {t.title}?"
    return AgentOutput(
        message=(
            f"Good question to investigate: “{q}”. I'll separate what's actually evidenced from "
            "what's speculation before drawing any conclusion."
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
                question="Should I prioritize primary sources/data, or a broader survey of existing takes?",
                context=f"Scoping the research for: {t.title}",
                importance=InterruptionPolicy.NEEDS_DECISION,
            )
        ],
    )


def _content(agent: Agent, t: Thought) -> AgentOutput:
    text = _text(t)
    hit = _any(text, ("content", "idea", "video", "post", "write", "story", "hook", "audience",
                       "narrative", "essay", "thread", "newsletter", "topic", "blog"))
    if not hit:
        return AgentOutput(
            relevant=False,
            skip_reason="No content angle worth developing here.",
        )
    return AgentOutput(
        message=(
            f"There's a content angle in “{t.title}” ('{hit}'). Hook idea: lead with the specific "
            "tension in this thought rather than the general topic — specificity is what makes "
            "people stop scrolling."
        ),
        tasks=[
            TaskProposal(
                title=f"Draft content outline: {t.title}",
                description="Lead with the hook; keep the user's exploratory voice.",
                priority=Priority.MEDIUM,
                rationale="Thought has a genuine content angle.",
            )
        ],
        memory_updates=[
            MemoryUpdate(scope=MemoryScope.AGENT, category="Content ideas", content=t.title)
        ],
    )


def _documentary(agent: Agent, t: Thought) -> AgentOutput:
    # Deliberately restrained — not every thought is documentary-worthy.
    text = _text(t)
    hit = _any(text, ("life", "journey", "story", "moment", "remember", "milestone", "arc",
                       "theme", "reflection", "timeline", "chapter"))
    if not hit:
        return AgentOutput(
            relevant=False,
            skip_reason="Not a milestone or recurring-theme moment worth logging to the timeline.",
        )
    return AgentOutput(
        message="",
        memory_updates=[
            MemoryUpdate(
                scope=MemoryScope.AGENT,
                category="Timeline",
                content=f"{t.created_at:%Y-%m-%d}: {t.title} ('{hit}').",
            )
        ],
        connections=[
            ConnectionProposal(
                type=ConnectionType.SHARED_THEME,
                title=f"Recurring theme: {hit}",
                explanation=f"This thought echoes the recurring '{hit}' thread in your timeline.",
                confidence=0.55,
                related_object_ids=[t.id],
            )
        ],
    )


def _behavior(agent: Agent, t: Thought) -> AgentOutput:
    text = _text(t)
    hit = _any(text, ("habit", "pattern", "behavior", "routine", "procrastinat", "motivation",
                       "discipline", "intention", "experiment"))
    if not hit:
        return AgentOutput(
            relevant=False,
            skip_reason="No recurring behavioral pattern here to compare against stated intentions.",
        )
    return AgentOutput(
        message=(
            f"“{t.title}” touches on a behavioral pattern ('{hit}'). I won't diagnose anything — "
            "but one cautious experiment: track whether this happens from low motivation or low "
            "capacity. They look similar but respond to different interventions."
        ),
        memory_updates=[
            MemoryUpdate(
                scope=MemoryScope.AGENT,
                category="Patterns",
                content=f"Pattern noted ('{hit}'): {t.title}",
            )
        ],
    )


def _builder(agent: Agent, t: Thought) -> AgentOutput:
    text = _text(t)
    hit = _any(text, ("build", "app", "project", "code", "feature", "prototype", "mvp", "ship",
                       "implement", "milestone", "software", "tool"))
    if not hit:
        return AgentOutput(
            relevant=False,
            skip_reason="Nothing concrete to build here yet.",
        )
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


def _career(agent: Agent, t: Thought) -> AgentOutput:
    text = _text(t)
    hit = _any(text, ("career", "job", "portfolio", "credibility", "promotion", "salary", "linkedin", "brand"))
    if not hit:
        return AgentOutput(
            relevant=False,
            skip_reason="No career-portfolio angle here — not every thought builds your brand.",
        )
    return AgentOutput(
        message=(
            f"“{t.title}” is portfolio-worthy — it demonstrates something a future employer or "
            f"client would want to see ('{hit}'). Worth logging as evidence, even before it's "
            "fully built out."
        ),
        memory_updates=[
            MemoryUpdate(scope=MemoryScope.AGENT, category="Portfolio evidence", content=t.title)
        ],
    )


def _systems(agent: Agent, t: Thought) -> AgentOutput:
    text = _text(t)
    hit = _any(text, ("system", "process", "workflow", "automat", "pipeline", "duplicate", "organize", "tooling"))
    if not hit:
        return AgentOutput(
            relevant=False,
            skip_reason="No repeated process or structural angle here.",
        )
    return AgentOutput(
        message=(
            f"“{t.title}” looks like a one-off, but the pattern underneath ('{hit}') is worth "
            "turning into a repeatable system rather than solving it ad hoc again next time."
        ),
        tasks=[
            TaskProposal(
                title=f"Sketch a repeatable system for: {t.title}",
                description="Capture the steps once, then make them reusable.",
                priority=Priority.LOW,
                rationale="Recurring process detected.",
            )
        ],
    )


def _confidence(agent: Agent, t: Thought) -> AgentOutput:
    text = _text(t)
    hit = _any(
        text,
        ("finally", "shipped", "nailed", "proud", "accomplish", "overcame", "figured out",
         "pulled off", "got through", "despite", "won ", "achieved"),
    )
    if not hit:
        return AgentOutput(
            relevant=False,
            skip_reason="No concrete evidence of a win or growth here — staying quiet so "
            "encouragement doesn't become noise.",
        )
    return AgentOutput(
        message=(
            f"Worth naming: “{t.title}” is real evidence, not just a nice moment — you came "
            f"through on something ('{hit}'). That should update how you see your own "
            "track record, not just feel good for a minute."
        ),
        memory_updates=[
            MemoryUpdate(scope=MemoryScope.AGENT, category="Evidence of growth", content=t.title)
        ],
    )


def _networking(agent: Agent, t: Thought) -> AgentOutput:
    text = _text(t)
    hit = _any(
        text,
        ("network", "connect", "introduc", "mentor", "community", "meetup", "collaborat",
         "reach out", "cofounder", "partner", "dm ", "email them", "message them"),
    )
    entities = t.entities if hasattr(t, "entities") else []
    if not hit and not entities:
        return AgentOutput(
            relevant=False,
            skip_reason="No specific person, group or community to connect with here.",
        )
    who = entities[0] if entities else "the right person"
    return AgentOutput(
        message=(
            f"There's a concrete outreach move in “{t.title}”: reach out to {who} specifically "
            f"about this ('{hit or 'mentioned directly'}') rather than letting it stay an intention."
        ),
        tasks=[
            TaskProposal(
                title=f"Reach out re: {t.title}",
                description=f"Send a short, specific message to {who} tied to this exact thought.",
                priority=Priority.MEDIUM,
                rationale="Concrete networking opportunity identified.",
            )
        ],
    )


def _opportunity(agent: Agent, t: Thought) -> AgentOutput:
    text = _text(t)
    hit = _any(
        text,
        ("opportunity", "monetiz", "sell", "pitch", "client", "revenue", "business", "startup",
         "launch", "market", "customer", "pricing", "pay for"),
    )
    if not hit:
        return AgentOutput(
            relevant=False,
            skip_reason="No realistic product/revenue/opportunity angle here.",
        )
    return AgentOutput(
        message=(
            f"There's a real opportunity angle in “{t.title}” ('{hit}'). Smallest next step: "
            "test the idea on 3-5 real people who'd plausibly pay before building anything further."
        ),
        tasks=[
            TaskProposal(
                title=f"Validate opportunity: {t.title}",
                description="Talk to 3-5 plausible buyers/users before investing further.",
                priority=Priority.MEDIUM,
                rationale="Thought has a tangible opportunity angle.",
            )
        ],
    )


def _growth(agent: Agent, t: Thought) -> AgentOutput:
    text = _text(t)
    hit = _any(
        text,
        ("improve", "skill", "practice", "weak at", "learn", "better at", "struggl", "stuck",
         "get better", "level up", "keep failing", "can't seem to"),
    )
    if not hit:
        return AgentOutput(
            relevant=False,
            skip_reason="No specific skill gap or improvement angle here.",
        )
    return AgentOutput(
        message=(
            f"“{t.title}” points to one specific thing worth practicing ('{hit}') — not a vague "
            "'work on yourself', but a bounded skill you could deliberately drill."
        ),
        tasks=[
            TaskProposal(
                title=f"Practice: {t.title}",
                description="Pick one small, repeatable drill for this specific gap this week.",
                priority=Priority.LOW,
                rationale="Concrete, bounded improvement angle identified.",
            )
        ],
    )


_GENERATORS = {
    "research": _research,
    "content": _content,
    "documentary": _documentary,
    "behavior": _behavior,
    "builder": _builder,
    "career": _career,
    "systems": _systems,
    "confidence": _confidence,
    "networking": _networking,
    "opportunity": _opportunity,
    "growth": _growth,
}
