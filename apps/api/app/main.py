"""Council API entrypoint."""

from __future__ import annotations

import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import (
    activity,
    agents,
    conversations,
    health,
    home,
    inbox,
    jobs,
    memory,
    projects,
    reports,
    research,
    search,
    storage,
    tasks,
    thoughts,
    voice,
)
from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger, request_id_ctx

settings = get_settings()
configure_logging(settings.log_level)
log = get_logger("council.api")

app = FastAPI(
    title="Council API",
    version="0.1.0",
    description="Voice-first personal cognitive OS of persistent specialist AI agents.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_context(request: Request, call_next):
    rid = request.headers.get("x-request-id") or uuid.uuid4().hex[:12]
    request_id_ctx.set(rid)
    log.info("request", method=request.method, path=request.url.path)
    try:
        response = await call_next(request)
    except Exception as exc:  # structured error surface
        log.error("unhandled_error", error=str(exc), path=request.url.path)
        return JSONResponse(status_code=500, content={"detail": "internal error", "request_id": rid})
    response.headers["x-request-id"] = rid
    return response


for _router in (
    health.router,
    home.router,
    thoughts.router,
    agents.router,
    tasks.router,
    projects.router,
    memory.router,
    reports.router,
    research.router,
    inbox.router,
    activity.router,
    search.router,
    voice.router,
    conversations.router,
    jobs.router,
    storage.router,
):
    app.include_router(_router)


@app.get("/")
async def root():
    return {
        "name": "Council API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
        "provider_mode": settings.provider_mode,
    }
