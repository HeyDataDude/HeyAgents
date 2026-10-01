"use client";

import { FileText, Mic, Star } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import { StatusBadge } from "@/components/ui/badges";
import { PageContainer, PageHeader } from "@/components/ui/page";
import { EmptyState, LoadingBlock } from "@/components/ui/states";
import { useThoughts } from "@/lib/hooks";
import { useUI } from "@/lib/store";
import { timeAgo } from "@/lib/utils";

const FILTERS = [
  { key: "", label: "All" },
  { key: "ready_for_review", label: "Unprocessed" },
  { key: "dispatched", label: "Dispatched" },
];

export default function ThoughtsPage() {
  const [status, setStatus] = useState("");
  const { data, isLoading } = useThoughts(status ? { status } : {});
  const openTalk = useUI((s) => s.openTalk);

  return (
    <PageContainer>
      <PageHeader
        title="Thoughts"
        description="A timeline of everything you've thought out loud."
        action={
          <button onClick={openTalk} className="btn btn-primary">
            <Mic className="h-4 w-4" /> New thought
          </button>
        }
      />

      <div className="mb-4 flex gap-1.5">
        {FILTERS.map((f) => (
          <button
            key={f.key}
            onClick={() => setStatus(f.key)}
            className={`chip cursor-pointer ${status === f.key ? "border-accent bg-accent/10 text-fg" : ""}`}
          >
            {f.label}
          </button>
        ))}
      </div>

      {isLoading ? (
        <LoadingBlock />
      ) : data?.items.length ? (
        <div className="space-y-2">
          {data.items.map((t) => (
            <Link
              key={t.id}
              href={`/thoughts/${t.id}`}
              className="card block px-4 py-3 transition-colors hover:bg-surface-2"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    {t.capture_mode === "voice" ? (
                      <Mic className="h-3.5 w-3.5 text-muted" />
                    ) : (
                      <FileText className="h-3.5 w-3.5 text-muted" />
                    )}
                    <span className="truncate font-medium">{t.title}</span>
                    {t.starred && <Star className="h-3.5 w-3.5 fill-amber-400 text-amber-400" />}
                  </div>
                  <p className="mt-1 line-clamp-2 text-sm text-fg-subtle">{t.summary || t.clean_transcript}</p>
                  <div className="mt-2 flex flex-wrap items-center gap-1.5">
                    {t.topics.slice(0, 4).map((topic) => (
                      <span key={topic} className="chip">{topic}</span>
                    ))}
                  </div>
                </div>
                <div className="flex shrink-0 flex-col items-end gap-1.5">
                  <StatusBadge status={t.status} />
                  <span className="text-[11px] text-muted">{timeAgo(t.created_at)}</span>
                </div>
              </div>
            </Link>
          ))}
        </div>
      ) : (
        <EmptyState
          icon={FileText}
          title="No thoughts yet"
          description="Press Talk and say whatever's on your mind. Council does the organizing."
          action={
            <button onClick={openTalk} className="btn btn-primary">
              <Mic className="h-4 w-4" /> Start talking
            </button>
          }
        />
      )}
    </PageContainer>
  );
}
