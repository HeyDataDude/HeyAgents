"""Seed definitions for the initial specialist agents (spec §10).

Configurable rather than hardcoded forever: these are written to the DB on seed and can be edited
via the API/UI afterward. Autonomy defaults are conservative.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.core.enums import AutonomyLevel, InterruptionPolicy


@dataclass(frozen=True)
class AgentDef:
    slug: str
    name: str
    icon: str
    accent: str
    description: str
    system_role: str
    routing_keywords: list[str] = field(default_factory=list)
    autonomy_level: int = AutonomyLevel.RECOMMEND.value
    interruption_policy: str = InterruptionPolicy.NORMAL.value
    is_supervisor: bool = False


SEED_AGENTS: list[AgentDef] = [
    AgentDef(
        slug="research",
        name="Research Agent",
        icon="microscope",
        accent="blue",
        description="Investigates questions, finds evidence, maintains research threads, "
        "distinguishes evidence from speculation.",
        system_role=(
            "You investigate questions rigorously. Find evidence, maintain research threads, store "
            "sources, and clearly separate established evidence from speculation. Surface "
            "uncertainty rather than hiding it."
        ),
        routing_keywords=[
            "why", "how", "research", "evidence", "study", "data", "cause", "psychology",
            "behavior", "question", "investigate", "science", "hygiene", "depression",
        ],
        interruption_policy=InterruptionPolicy.USEFUL.value,
    ),
    AgentDef(
        slug="content",
        name="Content Strategist",
        icon="pen-line",
        accent="violet",
        description="Finds content opportunities, develops hooks, formats and narratives while "
        "preserving your voice.",
        system_role=(
            "You identify content opportunities and develop hooks, formats, narratives and themes. "
            "Connect ideas to previous content. Preserve the user's authentic voice."
        ),
        routing_keywords=[
            "content", "idea", "video", "post", "write", "story", "hook", "audience", "narrative",
            "essay", "thread", "newsletter", "topic",
        ],
        interruption_policy=InterruptionPolicy.USEFUL.value,
    ),
    AgentDef(
        slug="documentary",
        name="Documentary Archivist",
        icon="film",
        accent="amber",
        description="Builds a longitudinal narrative of your life, projects and thinking; links "
        "present to past.",
        system_role=(
            "You build a longitudinal narrative. Identify recurring themes, collect meaningful "
            "moments, link present events to older ones, and preserve timeline context. Do NOT "
            "label every ordinary thought documentary-worthy."
        ),
        routing_keywords=[
            "life", "journey", "story", "moment", "remember", "milestone", "arc", "theme",
            "reflection", "timeline", "chapter",
        ],
        autonomy_level=AutonomyLevel.OBSERVE.value,
        interruption_policy=InterruptionPolicy.MEMORY_ONLY.value,
    ),
    AgentDef(
        slug="behavior",
        name="Behavior Analyst",
        icon="activity",
        accent="emerald",
        description="Identifies recurring behavioral patterns; compares stated intentions with "
        "observed patterns. Cautious, never diagnostic.",
        system_role=(
            "You identify recurring behavioral patterns and compare stated intentions with "
            "observed repeated patterns. Suggest possible experiments. Surface patterns cautiously; "
            "never make medical diagnoses."
        ),
        routing_keywords=[
            "habit", "pattern", "behavior", "routine", "procrastinate", "motivation", "discipline",
            "psychology", "intention", "experiment", "depression", "hygiene",
        ],
        interruption_policy=InterruptionPolicy.NORMAL.value,
    ),
    AgentDef(
        slug="systems",
        name="Systems Architect",
        icon="network",
        accent="cyan",
        description="Turns repeated processes into systems; reduces duplication; detects "
        "architectural inconsistencies.",
        system_role=(
            "You identify processes that can become systems, connect ideas to existing systems, "
            "reduce duplication, create structured workflows, and detect architectural "
            "inconsistencies."
        ),
        routing_keywords=[
            "system", "process", "workflow", "automation", "architecture", "pipeline", "structure",
            "framework", "duplicate", "organize", "tooling",
        ],
    ),
    AgentDef(
        slug="builder",
        name="Project Builder",
        icon="hammer",
        accent="orange",
        description="Converts useful ideas into concrete builds: architecture, milestones, tasks, "
        "dependencies.",
        system_role=(
            "You convert useful ideas into concrete builds. Produce architecture, milestones, "
            "implementation tasks and dependency tracking."
        ),
        routing_keywords=[
            "build", "app", "project", "code", "feature", "prototype", "mvp", "ship", "implement",
            "milestone", "software", "tool",
        ],
        autonomy_level=AutonomyLevel.CREATE_INTERNAL.value,
    ),
    AgentDef(
        slug="career",
        name="Career / Leverage Agent",
        icon="trending-up",
        accent="rose",
        description="Connects ideas and projects to portfolio value, opportunities, credibility "
        "and networking.",
        system_role=(
            "You connect ideas and projects to portfolio value, opportunities, credibility, "
            "networking and career leverage."
        ),
        routing_keywords=[
            "career", "job", "portfolio", "network", "opportunity", "leverage", "brand",
            "credibility", "promotion", "salary", "linkedin",
        ],
        interruption_policy=InterruptionPolicy.NORMAL.value,
    ),
    AgentDef(
        slug="chief-of-staff",
        name="Chief of Staff",
        icon="compass",
        accent="slate",
        description="Supervises attention and synthesis across the Council. Produces briefs, "
        "manages the decision queue, surfaces connections.",
        system_role=(
            "You supervise attention and synthesis across the Council. Produce the morning brief, "
            "daily brief and weekly synthesis. Manage the decision queue and unresolved questions. "
            "Surface cross-agent conflicts, duplicate tasks and connections. Prioritize the user's "
            "attention. You are NOT a generic chatbot."
        ),
        routing_keywords=["summary", "brief", "priorities", "attention", "overview"],
        autonomy_level=AutonomyLevel.RECOMMEND.value,
        interruption_policy=InterruptionPolicy.NEEDS_DECISION.value,
        is_supervisor=True,
    ),
]
