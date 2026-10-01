from __future__ import annotations

from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    limit: int
    offset: int


class ObjectRef(BaseModel):
    type: str
    id: str
    label: str = ""


class TimeRange(BaseModel):
    start: datetime | None = None
    end: datetime | None = None
