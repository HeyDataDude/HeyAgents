"use client";

import { Activity as ActivityIcon } from "lucide-react";
import Link from "next/link";

import { PageContainer, PageHeader } from "@/components/ui/page";
import { EmptyState, LoadingBlock } from "@/components/ui/states";
import { useActivity, useConnections } from "@/lib/hooks";
import { timeAgo } from "@/lib/utils";

export default function ActivityPage() {
  const { data, isLoading } = useActivity();
  const { data: connections } = useConnections();

  return (
    <PageContainer>
      <PageHeader title="Activity" description="A live, link-rich view of what the system is doing." />

      <div className="grid gap-6 lg:grid-cols-[1fr_320px]">
        <div>
          {isLoading ? (
            <LoadingBlock />
          ) : data?.items.length ? (
            <div className="space-y-1">
              {data.items.map((a) => (
                <div key={a.id} className="flex gap-3 rounded-md px-2 py-2 hover:bg-surface-2">
                  <span className={`mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full ${a.level === "error" ? "bg-red-500" : "bg-accent"}`} />
                  <div className="min-w-0 flex-1">
                    <p className="text-sm">{a.message}</p>
                    <div className="mt-0.5 flex items-center gap-2 text-[11px] text-muted">
                      <span className="font-medium">{a.actor}</span>
                      <span>·</span>
                      <span>{timeAgo(a.created_at)}</span>
                      {a.links.map((l) => (
                        <Link key={l.id} href={l.type === "thought" ? `/thoughts/${l.id}` : "#"} className="text-accent hover:underline">
                          {l.label || l.type}
                        </Link>
                      ))}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <EmptyState icon={ActivityIcon} title="No activity yet" />
          )}
        </div>

        <aside>
          <h2 className="section-label mb-2">Connections</h2>
          <div className="space-y-2">
            {(connections?.items ?? []).map((c) => (
              <div key={c.id} className="card p-3">
                <div className="mb-1 flex items-center justify-between">
                  <span className="chip capitalize">{c.type.replace(/_/g, " ")}</span>
                  <span className="font-mono text-[11px] text-muted">{c.confidence.toFixed(2)}</span>
                </div>
                <p className="text-sm font-medium">{c.title}</p>
                <p className="mt-0.5 text-xs text-muted">{c.explanation}</p>
              </div>
            ))}
            {!connections?.items.length && <p className="text-sm text-muted">No connections discovered yet.</p>}
          </div>
        </aside>
      </div>
    </PageContainer>
  );
}
