"""Shared column helpers: portable JSON + optional pgvector embedding column.

The embedding column degrades gracefully to JSON on SQLite (used in tests) so the models load
everywhere, while using a real pgvector `Vector` type on PostgreSQL.
"""

from __future__ import annotations

from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import TypeDecorator

try:  # pragma: no cover - import guarded for environments without pgvector
    from pgvector.sqlalchemy import Vector as _PGVector

    HAS_PGVECTOR = True
except Exception:  # pragma: no cover
    _PGVector = None
    HAS_PGVECTOR = False


# JSON that uses JSONB on Postgres and plain JSON elsewhere.
JSONColumn = JSON().with_variant(JSONB(), "postgresql")


class Embedding(TypeDecorator):
    """Vector column that uses pgvector on Postgres and JSON (list[float]) elsewhere."""

    impl = JSON
    cache_ok = True

    def __init__(self, dim: int = 1536, *args, **kwargs):
        self.dim = dim
        super().__init__(*args, **kwargs)

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql" and HAS_PGVECTOR:
            return dialect.type_descriptor(_PGVector(self.dim))
        return dialect.type_descriptor(JSON())
