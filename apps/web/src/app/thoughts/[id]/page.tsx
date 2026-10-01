"use client";

import { ArrowLeft, Play } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";

import { StatusBadge } from "@/components/ui/badges";
import { PageContainer } from "@/components/ui/page";
import { LoadingBlock } from "@/components/ui/states";
import { api } from "@/lib/api";
import { useThoughtDetail } from "@/lib/hooks";
import { timeAgo } from "@/lib/utils";

export default function ThoughtDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { data, isLoading } = useThoughtDetail(id);

  if (isLoading || !data) return <PageContainer><LoadingBlock /></PageContainer>;

  const t = data.thought;
  const audioUrl = api.storageUrl(t.original_audio_uri);

  return (
    <PageContainer>
      <Link href="/thoughts" className="mb-4 inline-flex items-center gap-1.5 text-sm text-muted hover:text-fg">
        <ArrowLeft className="h-4 w-4" /> Thoughts
      </Link>

      <div className="mb-1 flex items-center gap-2">
        <h1 className="text-xl font-semibold tracking-tight">{t.title}</h1>
        <StatusBadge status={t.status} />
      </div>
      <p className="mb-6 text-sm text-muted">{timeAgo(t.created_at)} · {t.thought_type}</p>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          <Card title="Clean thought">
            <p className="text-sm leading-relaxed">{t.clean_transcript}</p>
          </Card>

          <Card title="Raw transcript">
            <p className="text-sm italic leading-relaxed text-fg-subtle">{t.raw_transcript}</p>
            {audioUrl && (
              <a href={audioUrl} target="_blank" rel="noreferrer" className="btn mt-3 h-8 text-xs">
                <Play className="h-3.5 w-3.5" /> Listen to original
              </a>
            )}
          </Card>

          <Card title="Agent responses">
            {data.agent_dispatches.length ? (
              <div className="space-y-3">
                {data.agent_dispatches.map((d: any) => (
                  <div key={d.id} className="rounded-md border p-3">
                    <div className="mb-1 flex items-center justify-between">
                      <Link href={`/agents/${d.agent_id}`} className="text-sm font-medium hover:underline">
                        {d.agent_id}
                      </Link>
                      <div className="flex items-center gap-2">
                        <span className="chip">{d.response_mode}</span>
                        <StatusBadge status={d.status} />
                      </div>
                    </div>
                    <p className="text-sm text-fg-subtle">{d.response_summary || "(no message)"}</p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted">Not dispatched to any agents yet.</p>
            )}
          </Card>
        </div>

        <div className="space-y-6">
          <Card title="Structured extraction">
            <Field label="Topics" items={t.topics} />
            <Field label="Questions" items={t.questions} />
            <Field label="Ideas" items={t.ideas} />
            <Field label="Possible actions" items={t.possible_actions} />
            <Field label="Entities" items={t.entities} />
          </Card>

          <Card title="Derived items">
            <DerivedRow label="Tasks" count={data.tasks.length} href="/tasks" />
            <DerivedRow label="Research jobs" count={data.research_jobs.length} />
            <DerivedRow label="Memories updated" count={data.memories.length} href="/memory" />
          </Card>
        </div>
      </div>
    </PageContainer>
  );
}

function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="card p-4">
      <h3 className="section-label mb-2.5">{title}</h3>
      {children}
    </section>
  );
}

function Field({ label, items }: { label: string; items: string[] }) {
  if (!items?.length) return null;
  return (
    <div className="mb-3 last:mb-0">
      <div className="mb-1 text-xs font-medium text-muted">{label}</div>
      <div className="flex flex-wrap gap-1.5">
        {items.map((it, i) => (
          <span key={i} className="chip">{it}</span>
        ))}
      </div>
    </div>
  );
}

function DerivedRow({ label, count, href }: { label: string; count: number; href?: string }) {
  const content = (
    <div className="flex items-center justify-between py-1.5 text-sm">
      <span className="text-fg-subtle">{label}</span>
      <span className="font-medium tabular-nums">{count}</span>
    </div>
  );
  return href ? <Link href={href} className="block hover:text-fg">{content}</Link> : content;
}
