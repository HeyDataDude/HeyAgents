from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.search import SearchService

router = APIRouter(prefix="/api/search", tags=["search"])


@router.get("")
async def search(q: str = Query(""), db: AsyncSession = Depends(get_db)):
    svc = SearchService(db)
    results = await svc.search(q)
    return {"query": q, "results": results}
