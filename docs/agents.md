# Council — Agents

Agents are **persistent specialists**, not chatbot personas. Each has its own memory, inbox,
autonomy level and interruption policy, and processes thoughts through its own lens.

## Seed specialists (`app/services/agents/definitions.py`)

| Slug | Name | Lens | Default autonomy |
|------|------|------|------------------|
| `research` | Research Agent | investigate, evidence vs speculation, research threads | Recommend |
| `content` | Content Strategist | hooks, formats, narratives, preserve voice | Recommend |
| `documentary` | Documentary Archivist | longitudinal narrative; restrained | Observe |
| `behavior` | Behavior Analyst | patterns, intention vs behavior; cautious, non-diagnostic | Recommend |
| `systems` | Systems Architect | processes → systems, reduce duplication | Recommend |
| `builder` | Project Builder | ideas → architecture, milestones, tasks | Create internal |
| `career` | Career / Leverage | portfolio value, opportunities, networking | Recommend |
| `chief-of-staff` | Chief of Staff | **supervisor**: briefs, decision queue, synthesis | Recommend |

Agents are seeded to the DB and **editable** at runtime (Settings → Agents, or `PATCH /api/agents`).

## Agent Output Contract (`app/schemas/agent_output.py`)

Every execution returns a validated object — never just text:

```json
{
  "message": "...",
  "memory_updates": [],
  "tasks": [],
  "research_jobs": [],
  "project_updates": [],
  "questions_for_user": [],
  "connections": [],
  "artifacts": [],
  "notification_request": null
}
```

Invalid output is rejected (Pydantic) and falls back to a safe mock. Side effects are applied in
`app/services/agents/apply.py`.

## Autonomy levels

```
0 Observe                 — memory + connections only
1 Recommend               — + questions; tasks created but require approval
2 Create internal         — + internal tasks/drafts/research without approval
3 External with approval  — external actions allowed, each requires approval
4 External whitelisted    — explicitly whitelisted external actions auto-run
```

No external communication, purchasing, deletion, publishing or account modification happens
autonomously without explicit configuration.

## Response modes

`TALK` (conversational) · `QUICK` (fast concise) · `DEEP` (durable research job) ·
`REMEMBER` (memory only, no message) · `AUTO` (agent chooses the combination).

## Runner

`app/services/agents/runner.py` — mock mode uses tailored, deterministic specialist generators; live
mode calls the LLM (and the persistent Letta agent) with a strict system prompt + JSON schema.
