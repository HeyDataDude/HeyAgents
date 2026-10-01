# Council API

FastAPI backend for Council. See [`../../docs/development.md`](../../docs/development.md) to run it,
and [`../../docs/architecture.md`](../../docs/architecture.md) for design.

```
app/
  core/          config, logging, enums, ids
  db/            engine/session + declarative base
  models/        ORM: Thought, Agent, Dispatch, AgentDispatch, Memory, Task, Project,
                 ResearchJob, Report, AgentQuestion, Connection, Job, Activity, Conversation
  schemas/       Pydantic request/response + the Agent Output Contract
  services/      intake, thought_refiner, routing, dispatch, agents/, memory, research,
                 reports (Chief of Staff), intelligence, search, jobs, activity
  integrations/  provider interfaces + mock + live adapters (STT/LLM/embeddings/TTS/
                 research/Letta/LiveKit/storage) + factory
  api/           routers (thoughts, agents, tasks, projects, memory, reports, research,
                 inbox, activity, search, voice, conversations, jobs, home, storage, health)
  workers/       durable background worker
  scripts/       seed
alembic/         migrations
tests/           pytest (offline, SQLite + mock providers)
```
