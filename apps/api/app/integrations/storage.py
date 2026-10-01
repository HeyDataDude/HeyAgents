"""Object storage providers: local filesystem (dev) and S3-compatible (prod/MinIO)."""

from __future__ import annotations

import asyncio
from pathlib import Path

from app.core.config import Settings
from app.integrations.base import StorageProvider


class LocalStorageProvider(StorageProvider):
    name = "local"

    def __init__(self, base_dir: str):
        self.base = Path(base_dir)
        self.base.mkdir(parents=True, exist_ok=True)

    async def put(self, key: str, data: bytes, *, content_type: str = "application/octet-stream") -> str:
        path = self.base / key
        path.parent.mkdir(parents=True, exist_ok=True)
        await asyncio.to_thread(path.write_bytes, data)
        return self.url_for(key)

    async def get(self, key: str) -> bytes:
        path = self.base / key
        return await asyncio.to_thread(path.read_bytes)

    def url_for(self, key: str) -> str:
        # Served by the API via /api/storage/{key}
        return f"local://{key}"


class S3StorageProvider(StorageProvider):
    name = "s3"

    def __init__(self, settings: Settings):
        import boto3  # imported lazily so mock/local mode needs no boto3

        self._bucket = settings.s3_bucket
        self._client = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint_url or None,
            region_name=settings.s3_region,
        )

    async def put(self, key: str, data: bytes, *, content_type: str = "application/octet-stream") -> str:
        await asyncio.to_thread(
            self._client.put_object,
            Bucket=self._bucket,
            Key=key,
            Body=data,
            ContentType=content_type,
        )
        return self.url_for(key)

    async def get(self, key: str) -> bytes:
        obj = await asyncio.to_thread(self._client.get_object, Bucket=self._bucket, Key=key)
        return obj["Body"].read()

    def url_for(self, key: str) -> str:
        return f"s3://{self._bucket}/{key}"
