from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.report import Report
from app.services.report_pdf import render_report_pdf
from app.services.reports import ReportService

router = APIRouter(prefix="/api/reports", tags=["reports"])


def _ser(r: Report) -> dict:
    return {
        "id": r.id,
        "type": r.type,
        "title": r.title,
        "range_start": r.range_start,
        "range_end": r.range_end,
        "generated_by": r.generated_by,
        "content": r.content,
        "related_objects": r.related_objects,
        "created_at": r.created_at,
    }


@router.get("")
async def list_reports(db: AsyncSession = Depends(get_db), type: str | None = None):
    stmt = select(Report).order_by(Report.created_at.desc())
    if type:
        stmt = stmt.where(Report.type == type)
    rows = (await db.execute(stmt)).scalars().all()
    return {"items": [_ser(r) for r in rows]}


@router.get("/{report_id}")
async def get_report(report_id: str, db: AsyncSession = Depends(get_db)):
    r = await db.get(Report, report_id)
    if not r:
        raise HTTPException(404, "report not found")
    return _ser(r)


@router.get("/{report_id}/pdf")
async def get_report_pdf(report_id: str, db: AsyncSession = Depends(get_db)):
    r = await db.get(Report, report_id)
    if not r:
        raise HTTPException(404, "report not found")
    pdf_bytes = render_report_pdf(r)
    filename = f"{r.type}-brief-{r.id}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/generate")
async def generate_report(kind: str, db: AsyncSession = Depends(get_db)):
    svc = ReportService(db)
    if kind == "morning":
        r = await svc.generate_morning()
    elif kind == "daily":
        r = await svc.generate_daily()
    elif kind == "weekly":
        r = await svc.generate_weekly()
    else:
        raise HTTPException(400, "kind must be morning|daily|weekly")
    return _ser(r)
