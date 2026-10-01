# Council

> A voice-first personal cognitive operating system made of persistent specialist AI agents.

Council lets you **think out loud**. You speak a messy thought; Council records it, transcribes
it, cleans it (without changing meaning), extracts structure (topics, questions, ideas, possible
actions), recommends which specialist agents should see it, dispatches it, and lets each agent
process it through its own lens — producing responses, memory updates, tasks, research jobs,
project links, questions and connections. A Chief of Staff synthesizes everything into daily and
weekly briefs so you are never forced to read ten agent responses.

```
THINK → SPEAK → CONTINUE WITH LIFE
```

Council handles: capture, organization, routing, analysis, memory, research, tasks, connections,
synthesis and resurfacing.

---

## What this is (and isn't)

- **Is**: an organized personal intelligence system where thoughts, agents, tasks, projects,
  reports, memories and research jobs are **first-class objects**.
- **Is not**: a collection of chatbot personas. Chat is only one interface.

---

## Architecture at a glance

```
council/
├── apps/
│   ├── web/        # Next.js 14 (App Router) + TypeScript + Tailwind + shadcn-style UI
│   └── api/        # FastAPI + SQLAlchemy + Alembic + Pydantic
├── packages/
│   └── shared/     # Shared TypeScript types + domain enums (mirrors backend schemas)
├── infrastructure/
│   ├── docker/
│   └── migrations/ -> apps/api/alembic (symlinked conceptually; see docs)
├── docs/           # architecture, data-model, agents, voice, memory, development
├── docker-compose.yml
├── .env.example
└── README.md
```

See [`docs/architecture.md`](docs/architecture.md) for the full technology decisions, including
which external systems (Letta, LiveKit, Pipecat, faster-whisper, WhisperX) are *integrated* vs used
only as *references*, and how every external dependency is abstracted behind a provider interface
with a **mock implementation** so the system runs with zero API keys.

---

## Quick start

```bash
git clone <this repo>
cd council
cp .env.example .env

# Everything (Postgres + pgvector, Redis, API, worker, web) via Docker:
docker compose up -d

# Open:
#   Web UI    http://localhost:3000
#   API docs  http://localhost:8000/docs
#   Health    http://localhost:8000/health
```

On first boot the API runs migrations and **seeds demo data** (8 specialist agents, sample
thoughts, tasks, research jobs, projects, reports, memories and connections) so the full UI is
inspectable immediately — **no blank screens**, no API keys required.

### Local development (without Docker)

See [`docs/development.md`](docs/development.md). In short:

```bash
# Backend
cd apps/api
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
alembic upgrade head
python -m app.scripts.seed
uvicorn app.main:app --reload

# Frontend (separate terminal)
cd apps/web
pnpm install
pnpm dev
```

---

## Demo / mock mode

Council ships with **mock providers** for every external integration (LLM, STT, TTS, embeddings,
web research, agent-memory, object storage). When `COUNCIL_PROVIDER_MODE=mock` (the default), the
whole pipeline runs deterministically offline:

- STT returns a canned transcript for uploaded audio.
- The Thought Refiner cleans + extracts structure with a rule-based mock.
- Agents return schema-valid structured outputs.
- The Chief of Staff synthesizes briefs from real DB state.

Set `COUNCIL_PROVIDER_MODE=live` and configure provider keys in `.env` to use real models.

---

## The core loop (Definition of Done, Phase 1)

1. Open Council → press **Talk** → speak → stop.
2. Audio is stored (original preserved permanently).
3. Transcribe → **raw transcript** preserved.
4. **Refine** → clean transcript (meaning preserved, uncertainty kept).
5. **Extract** topics / questions / ideas / possible actions / entities.
6. **Recommend** agents with confidence scores.
7. Review screen → modify recipients → choose response mode
   (**Quick / Deep / Remember / Talk / Auto**).
8. **Dispatch** → one `AgentDispatch` row per recipient.
9. Agents process → responses, tasks, research jobs, memory updates, questions, connections.
10. Everything is browsable and traceable back to the originating thought.

---

## Project phases

| Phase | Scope | Status in this build |
|------|-------|----------------------|
| 0 | Monorepo, Docker, DB, migrations, API+web shells, config, logging, seed | **Implemented** |
| 1 | Core voice-thought loop (capture→dispatch→responses) | **Implemented** |
| 2 | Persistent agents + memory (Letta provider abstraction + mock) | **Implemented (mock), Letta adapter stubbed** |
| 3 | Structured outputs (tasks/notes/research/projects/questions/connections) | **Implemented** |
| 4 | Realtime voice + Council Call (LiveKit/Pipecat abstraction + mock) | **Interface + UI + mock** |
| 5 | Deep work durable queue + progress | **Implemented (job model + worker + mock)** |
| 6 | Chief of Staff briefs + decision inbox + synthesis | **Implemented** |
| 7 | Cross-agent intelligence (connections/themes/duplicates) | **Implemented (heuristic + provenance)** |

See [`docs/architecture.md`](docs/architecture.md) for exactly what each adapter does and where the
real integration plugs in.

---

## Privacy / local-first

Council may eventually hold an enormous amount of personal information. It is architected so that:

- storage paths and database ownership are explicit and local by default;
- no external uploads happen silently — providers are explicitly configured via `.env`;
- data can be exported and deleted;
- every derived object carries provenance back to its originating thought/audio.

See [`docs/architecture.md` §Privacy](docs/architecture.md#privacy--local-first).

---

## License

MIT. See `LICENSE`.
