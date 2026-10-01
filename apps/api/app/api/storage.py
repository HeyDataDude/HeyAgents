from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from app.integrations.factory import get_providers

router = APIRouter(prefix="/api/storage", tags=["storage"])


@router.get("/{key:path}")
async def get_object(key: str):
    """Serve stored objects (audio, artifacts). Local backend reads from disk."""
    providers = get_providers()
    try:
        data = await providers.storage.get(key)
    except Exception as exc:
        raise HTTPException(404, "object not found") from exc
    content_type = "application/octet-stream"
    if key.endswith(".md"):
        content_type = "text/markdown"
    elif key.endswith(".webm"):
        content_type = "audio/webm"
    elif key.endswith(".wav"):
        content_type = "audio/wav"
    return Response(content=data, media_type=content_type)
