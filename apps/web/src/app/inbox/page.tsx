"use client";

import { CheckCircle2 } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import { StatusBadge } from "@/components/ui/badges";
import { PageContainer, PageHeader } from "@/components/ui/page";
import { EmptyState, LoadingBlock } from "@/components/ui/states";
import { useAnswerQuestion, useInbox } from "@/lib/hooks";
import { timeAgo } from "@/lib/utils";

const TABS = [
  { key: "all", label: "All" },
  { key: "needs_decision", label: "Needs decision" },
  { key: "needs_review", label: "Needs review" },
  { key: "completed_work", label: "Completed" },
  { key: "agent_questions", label: "Questions" },
  { key: "failures", label: "Failures" },
];

export default function InboxPage() {
  const [tab, setTab] = useState("all");
  const { data, isLoading } = useInbox(tab);
  const answer = useAnswerQuestion();
  const [drafts, setDrafts] = useState<Record<string, string>>({});

  return (
    <PageContainer>
      <PageHeader title="Inbox" description="Everything that needs your attention, in one place." />

      <div className="mb-4 flex flex-wrap gap-1.5">
        {TABS.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`chip cursor-pointer ${tab === t.key ? "border-accent bg-accent/10 text-fg" : ""}`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {isLoading ? (
        <LoadingBlock />
      ) : data?.items.length ? (
        <div className="space-y-2">
          {data.items.map((item) => (
            <div key={`${item.kind}-${item.id}`} className="card p-4">
              <div className="mb-1 flex items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <span className="chip capitalize">{item.kind.replace(/_/g, " ")}</span>
                  {item.agent && <span className="text-xs font-medium text-fg-subtle">{item.agent}</span>}
                </div>
                <span className="text-[11px] text-muted">{timeAgo(item.created_at)}</span>
              </div>
              <p className="text-sm">{item.title}</p>
              {item.context && <p className="mt-1 text-xs text-muted">{item.context}</p>}

              {item.kind === "agent_question" && (
                <div className="mt-3 flex gap-2">
                  <input
                    value={drafts[item.id] ?? ""}
                    onChange={(e) => setDrafts((d) => ({ ...d, [item.id]: e.target.value }))}
                    placeholder="Your answer…"
                    className="input h-9"
                  />
                  <button
                    onClick={() => answer.mutate({ id: item.id, answer: drafts[item.id] ?? "" })}
                    disabled={!drafts[item.id]}
                    className="btn btn-primary h-9 shrink-0"
                  >
                    Answer
                  </button>
                </div>
              )}
              {item.thought_id && item.kind !== "agent_question" && (
                <Link href={`/thoughts/${item.thought_id}`} className="mt-2 inline-block text-xs text-accent hover:underline">
                  View thought →
                </Link>
              )}
            </div>
          ))}
        </div>
      ) : (
        <EmptyState icon={CheckCircle2} title="Inbox zero" description="You're all caught up." />
      )}
    </PageContainer>
  );
}
