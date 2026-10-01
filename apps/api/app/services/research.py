"""Deep research executor (spec §16 deep path).

Runs a ResearchJob to completion with progress updates. Uses the research provider to gather
sources and the LLM to synthesize findings. In mock mode this is deterministic and offline.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import ResearchStatus
from app.core.logging import get_logger
from app.integrations.base import LLMMessage
from app.integrations.factory import get_providers
from app.models.research import ResearchJob
from app.services.activity import record_activity

log = get_logger("council.research")


class ResearchExecutor:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.providers = get_providers()

    async def run(self, job: ResearchJob) -> ResearchJob:
        job.status = ResearchStatus.RESEARCHING.value
        job.progress = 10
        await self.db.flush()

        try:
            sources = await self.providers.research.search(job.question, max_results=5)
            job.sources = [
                {"title": s.title, "url": s.url, "snippet": s.snippet} for s in sources
            ]
            job.progress = 60
            await self.db.flush()

            context = "\n".join(f"- {s.title}: {s.snippet}" for s in sources)
            findings = await self.providers.llm.complete(
                [
                    LLMMessage(
                        "system",
                        "Synthesize research findings. Separate evidence from speculation. Note "
                        "uncertainty explicitly. Be concise.",
                    ),
                    LLMMessage("user", f"Question: {job.question}\n\nSources:\n{context}"),
                ]
            )
            job.findings = findings
            job.progress = 100
            job.status = ResearchStatus.COMPLETED.value

            # Persist a findings artifact to storage.
            key = f"artifacts/research/{job.id}.md"
            md = f"# Research: {job.question}\n\n{findings}\n\n## Sources\n" + "\n".join(
                f"- [{s['title']}]({s['url']})" for s in job.sources
            )
            job.artifact_uri = await self.providers.storage.put(
                key, md.encode(), content_type="text/markdown"
            )
            await record_activity(
                self.db, kind="research", actor="research",
                message=f"Research complete: “{job.question[:60]}”",
                links=[{"type": "research", "id": job.id, "label": job.question[:60]}],
            )
        except Exception as exc:
            log.error("research_failed", error=str(exc))
            job.status = ResearchStatus.FAILED.value
            job.error = str(exc)
        return job
