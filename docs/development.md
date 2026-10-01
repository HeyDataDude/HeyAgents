# Council — Development

## Prerequisites
- Docker + Docker Compose (easiest path), **or**
- Python 3.11+, Node 20+, PostgreSQL 16 (+pgvector), Redis.

## Fastest: Docker

```bash
cp .env.example .env
docker compose up -d
# web:  http://localhost:3000
# api:  http://localhost:8000/docs
```

On boot the API runs migrations and seeds demo data (idempotent). Everything is inspectable
immediately in `mock` mode — no API keys needed.

## Backend (local, without Docker)

```bash
cd apps/api
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"            # add ".[live]" for faster-whisper/openai/letta

export COUNCIL_DATABASE_URL=postgresql+asyncpg://council:council@localhost:5432/council
export COUNCIL_DATABASE_URL_SYNC=postgresql+psycopg://council:council@localhost:5432/council

alembic upgrade head
python -m app.scripts.seed
uvicorn app.main:app --reload
```

Run the worker in another terminal:

```bash
cd apps/api && source .venv/bin/activate
python -m app.workers.worker
```

### Tests

```bash
cd apps/api
pytest                 # uses in-memory SQLite + mock providers; fully offline
```

Covered: thought creation, transcription interface, refinement schema, routing, dispatch creation,
agent output parsing, task creation, memory update handling, job state transitions, report
generation, autonomy restrictions, and a full create→refine→route→dispatch→response e2e.

## Frontend (local)

```bash
cd apps/web
pnpm install        # or npm install
pnpm dev            # http://localhost:3000
pnpm test           # vitest
pnpm typecheck
```

Set `NEXT_PUBLIC_API_BASE_URL` if the API isn't on `http://localhost:8000`.

## Going live (real providers)

Edit `.env`:

```
COUNCIL_PROVIDER_MODE=live
COUNCIL_LLM_PROVIDER=openai            OPENAI_API_KEY=sk-...
COUNCIL_STT_PROVIDER=faster_whisper
COUNCIL_EMBEDDING_PROVIDER=openai
COUNCIL_AGENT_MEMORY_PROVIDER=letta    LETTA_BASE_URL=...  LETTA_API_KEY=...
COUNCIL_REALTIME_PROVIDER=livekit      LIVEKIT_URL=...  LIVEKIT_API_KEY=...  LIVEKIT_API_SECRET=...
```

Providers are independent — bring them up one at a time; the rest stays on mock.

## Project layout

```
apps/api   FastAPI backend (models, schemas, services, api, workers, integrations, scripts)
apps/web   Next.js frontend (app router pages + components + lib hooks/api/store)
packages/shared  shared TS enums/types mirroring the backend
docs       architecture, data-model, agents, memory, voice, development
```

## Make targets

```bash
make up        # docker compose up -d
make down      # docker compose down
make seed      # re-run seed in the api container
make test      # backend tests in the api container
make logs      # tail all services
```
