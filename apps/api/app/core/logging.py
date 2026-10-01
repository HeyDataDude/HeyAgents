"""Structured logging + request-scoped correlation IDs.

Uses structlog so every log line is JSON with a request_id / job_id / agent_run_id when available.
"""

from __future__ import annotations

import logging
import sys
from contextvars import ContextVar

import structlog

request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)
job_id_ctx: ContextVar[str | None] = ContextVar("job_id", default=None)
agent_run_id_ctx: ContextVar[str | None] = ContextVar("agent_run_id", default=None)


def _inject_context(_logger, _method, event_dict):
    for key, ctx in (
        ("request_id", request_id_ctx),
        ("job_id", job_id_ctx),
        ("agent_run_id", agent_run_id_ctx),
    ):
        value = ctx.get()
        if value is not None:
            event_dict[key] = value
    return event_dict


def configure_logging(level: str = "INFO") -> None:
    logging.basicConfig(format="%(message)s", stream=sys.stdout, level=level.upper())
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            _inject_context,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, level.upper(), logging.INFO)
        ),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = "council") -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)
