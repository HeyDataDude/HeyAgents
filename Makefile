.PHONY: up down build seed test logs api-shell migrate web-dev api-dev worker

up:
	docker compose up -d --build

down:
	docker compose down

build:
	docker compose build

seed:
	docker compose exec api python -m app.scripts.seed

migrate:
	docker compose exec api alembic upgrade head

test:
	docker compose exec api pytest

logs:
	docker compose logs -f

api-shell:
	docker compose exec api bash

# Local (non-docker) dev convenience
api-dev:
	cd apps/api && uvicorn app.main:app --reload

worker:
	cd apps/api && python -m app.workers.worker

web-dev:
	cd apps/web && pnpm dev
