# Council — Architecture

Council is a voice-first personal cognitive OS: you think out loud, and a council of persistent
specialist agents captures, organizes, routes, analyzes, remembers, researches and synthesizes.

This document records the system design and — per the build spec's "First Action" — the decisions
about which external open-source systems are **integrated** vs used only as **references**.

---

## 1. High-level shape

```
                       ┌──────────────────────────────────────────┐
   Browser (Next.js)   │  Talk · Home · Inbox · Agents · Thoughts   │
   polished command    │  Tasks · Projects · Reports · Memory ·     │
   center UI           │  Activity · Search · ⌘K palette            │
                       └───────────────┬────────────────────────────┘
                                       │ REST (JSON) + object storage
                       ┌───────────────▼────────────────────────────┐
   FastAPI backend     │  /api/thoughts /agents /dispatches /tasks   │
                       │  /projects /reports /memory /search /voice  │
                       │  /jobs /inbox /activity /home /system        │
                       ├─────────────────────────────────────────────┤
   Services            │  intake · thought_refiner · routing ·        │
                       │  dispatch · agents(runner/apply) · memory ·  │
                       │  research · reports(Chief of Staff) ·        │
                       │  intelligence · search · jobs                │
                       ├─────────────────────────────────────────────┤
   Provider interfaces │  LLM · STT · TTS · Embeddings · Research ·   │
   (+ mock + live)     │  AgentMemory(Letta) · Realtime(LiveKit) ·    │
                       │  Storage(local/S3)                           │
                       └───────┬───────────────────────┬──────────────┘
                               │                       │
                    PostgreSQL + pgvector         Redis + durable worker
                    (source of truth)             (deep work, reports)
```

The backend is the source of truth; everything a user needs is available through the API and
rendered in the UI. There is **no important state that lives only in logs, CLI or background magic**
(spec §44).

---

## 2. Domain model (first-class objects)

Council is explicitly **not** "loose chat JSON". Every concept is a typed table (see
[`data-model.md`](data-model.md)):

Thought · Dispatch · AgentDispatch · Agent · Memory (global/agent/project) · Task · Project ·
ResearchJob · Report · AgentQuestion · Connection · Job · Activity · Conversation/Message · User.

Every derived object preserves provenance back to its originating thought (and thereby the original
audio). See [`data-model.md` §Provenance](data-model.md#provenance).

---

## 3. The core loop (Phase 1)

`intake` → store audio (never overwritten) → STT → **raw transcript** (never overwritten) →
`thought_refiner` → **clean transcript** + structured extraction → `routing` recommendations →
Thought Review UI → `dispatch` (one `AgentDispatch` per recipient) → `agents.runner` →
`agents.apply` (autonomy-gated side effects) → responses/tasks/memory/research/questions/connections.

QUICK/REMEMBER/TALK/AUTO run inline; **DEEP** enqueues a durable `Job` processed by the worker.

---

## 4. Technology decisions

### Chosen stack
- **Frontend**: Next.js 14 (App Router), React 18, TypeScript, Tailwind, shadcn-style primitives,
  Lucide icons, TanStack Query, Zustand, next-themes. Aesthetic target: Linear/Raycast/Superhuman —
  calm, dense, premium; light + dark.
- **Backend**: Python 3.11, FastAPI, Pydantic v2, SQLAlchemy 2 (async), Alembic.
- **Database**: PostgreSQL 16 + **pgvector** for semantic retrieval. Structured data stays
  structured; vectors are a *booster*, never the only memory mechanism (spec §4).
- **Queue**: **Redis** as the wake-up channel + **a Postgres-backed durable `jobs` table** as the
  source of truth. See §6 for why we picked a custom lightweight dispatcher over Celery/Dramatiq/RQ.
- **Storage**: abstraction with `local` (dev / Docker volume) and `s3` (prod / MinIO) backends.

### External systems: integrate vs reference

| System | Decision | Rationale |
|--------|----------|-----------|
| **Letta** (stateful agents + long-term memory) | **Integrate** behind `AgentMemoryProvider`. Each Council `Agent` maps to a Letta agent via `letta_agent_id`. | Letta already solves persistent agent memory well; we use its API, not its UI. A mock provider ships so the system runs without Letta. Adapter: `integrations/live.py:LettaAgentMemoryProvider`. |
| **LiveKit Agents** (realtime voice) | **Integrate** behind `RealtimeVoiceProvider` for streaming STT/TTS, turn detection, barge-in. The API mints room tokens; a LiveKit agent worker joins the room. | Mature realtime stack; token minting is thin and vendor-owned capability. Mock provider returns a demo token so the Talk-to-agent UI works offline. |
| **Pipecat** | **Reference only** for now. | LiveKit covers the realtime path with less surface area for our single-user case. If multi-agent voice fan-out/handoff proves cleaner in Pipecat, the `RealtimeVoiceProvider` interface lets us swap without touching the rest of the system. Documented tradeoff rather than integrating both. |
| **faster-whisper** | **Integrate** behind `TranscriptionProvider` as the default recorded-speech STT. | Fast, high-quality local transcription. Adapter: `FasterWhisperProvider`. |
| **WhisperX** | **Reference / optional**. | Only materially better when we need word-level alignment or diarization; the provider abstraction allows selecting it per-need. Not a default dependency. |
| **Open WebUI / LibreChat** | **Reference only** (not integrated). | Studied for streaming messages, agent selectors, conversation management, attachment and memory UX. Council needs a purpose-built command-center interface, so we built our own rather than forking a chat app. |

**Principle:** we did not add a dependency just to use it. Each integration sits behind an interface
with a mock, so Council is always runnable and no vendor is load-bearing for *correctness of the
model* — only for *quality of the capability*.

---

## 5. Provider abstraction

`app/integrations/base.py` defines interfaces: `TranscriptionProvider`, `LLMProvider`,
`EmbeddingProvider`, `TTSProvider`, `ResearchProvider`, `AgentMemoryProvider`,
`RealtimeVoiceProvider`, `StorageProvider`.

`app/integrations/factory.py` resolves each from env settings. `COUNCIL_PROVIDER_MODE=mock` (default)
forces offline, deterministic implementations (`integrations/mock.py`) so the whole product runs with
zero API keys. Set per-provider settings + `COUNCIL_PROVIDER_MODE=live` to use real models. You can
mix (e.g. real STT + mock LLM) while bringing integrations up.

---

## 6. Durable jobs

Spec requires jobs to survive page refreshes and app restarts. We chose a **Postgres-backed job
table + Redis notification** instead of Celery/Dramatiq/RQ because:

- State must be *queryable* and *visible in the UI* (spec §16/§44); a dedicated `jobs` table gives
  first-class status/progress we can render, link and audit.
- The worker claims `QUEUED` jobs transactionally and marks them `WORKING`→`COMPLETED`/`FAILED`.
- On boot the worker **recovers orphans** (`WORKING` → `QUEUED`) so a crashed worker loses nothing.
- Redis `BLPOP` wakes the worker promptly; if Redis is down the worker **falls back to DB polling**,
  so jobs are never lost — they just run slightly later.

This keeps the operational surface small while meeting the durability + observability requirements.
Swapping in Celery later only touches `services/jobs.py` + `workers/worker.py`.

---

## 7. Autonomy & attention

- **Autonomy levels 0–4** are enforced in `services/agents/apply.py`. OBSERVE can only write memory
  + connections; RECOMMEND can ask questions and create approval-gated tasks; CREATE_INTERNAL can
  create internal tasks/research without approval; external actions always require approval unless
  explicitly whitelisted (level 4). No external comms/purchasing/deletion/publishing happens
  autonomously.
- **Interruption policy** per agent classifies results (URGENT … MEMORY_ONLY) so the user is not
  notified for every action. The global **Inbox** aggregates only what needs attention; the **Chief
  of Staff** synthesizes the rest into briefs (spec §13, §50).

---

## 8. Cross-agent intelligence

`services/intelligence.py` discovers shared themes, related thoughts (embedding cosine / topic
Jaccard) and duplicate tasks. **Every connection stores exactly which objects it links and why**
(provenance); nothing is fabricated to look busy (spec §17).

---

## 9. Failure handling (spec §48)

- STT failure → thought kept, status `FAILED`, error in `meta`, audio preserved; recoverable.
- LLM/refine failure → degrade to rule-based / raw-as-clean; thought still usable.
- One agent failing in a dispatch → isolated `FAILED` AgentDispatch; others still complete; dispatch
  becomes `PARTIAL`.
- Letta/LiveKit unavailable → mock provider or clear error; never a hard crash of the loop.
- Worker dies mid-job → orphan recovery re-queues on boot.
- Invalid agent output → Pydantic validation + fallback to a safe mock output.

---

## 10. Privacy / local-first

- Storage paths and DB ownership are explicit and **local by default** (Docker volumes).
- **No silent external uploads**: every provider is explicitly configured via `.env`; `mock` mode
  makes zero network calls.
- Data is **exportable** (artifacts + reports in object storage; DB is yours) and **deletable**
  (delete endpoints for thoughts/memory; cascade semantics documented in `data-model.md`).
- Provenance is pervasive, so you can always answer *who/why/from-which-thought/when*.
- When cloud providers are used it is visible in **Settings → Diagnostics** (provider table).

See also: [`data-model.md`](data-model.md), [`agents.md`](agents.md), [`memory.md`](memory.md),
[`voice.md`](voice.md), [`development.md`](development.md).
