# Council — Memory

Memory is **inspectable, not magic** (spec §31). Three scopes, never casually merged:

- **Global user memory** — facts useful to many agents: projects, goals, people, preferences,
  timeline, decisions.
- **Agent memory** — what one specialist has learned through its own lens.
- **Project / thread memory** — context belonging to a specific subject.

## Provenance

Every memory records `created_by_agent_id`, `originating_thought_id` and a `provenance` JSON blob,
so the Memory Explorer can show *when created*, *which agent*, and *which thought caused it*, with a
link straight back to the thought.

## Explorer UI (`/memory`)

Top-level GLOBAL / AGENTS / PROJECTS tree (`GET /api/memory/tree`), with search, inspect, edit and
delete. Deletion is explicit and user-controlled.

## Semantic retrieval

Memories carry an `embedding` (pgvector). Search is **hybrid**: lexical matching always applies;
embeddings boost ranking. Vectors are never the *only* mechanism — structured scope/category/
provenance remain primary.

## Persistent agent memory (Letta)

In live mode each Council agent maps to a Letta agent (`letta_agent_id`); long-term agent memory is
delegated to Letta via `AgentMemoryProvider`. Council still records memory rows for inspection +
provenance, keeping the user-facing explorer authoritative regardless of backend.
