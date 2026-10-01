"use client";

import { Check, ListTodo } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import { PriorityBadge, StatusBadge } from "@/components/ui/badges";
import { PageContainer, PageHeader } from "@/components/ui/page";
import { EmptyState, LoadingBlock } from "@/components/ui/states";
import { useTasks, useUpdateTask } from "@/lib/hooks";

const FILTERS = [
  { key: "", label: "All" },
  { key: "todo", label: "To do" },
  { key: "in_progress", label: "In progress" },
  { key: "done", label: "Done" },
];

export default function TasksPage() {
  const [status, setStatus] = useState("");
  const { data, isLoading } = useTasks(status ? { status } : {});
  const update = useUpdateTask();

  return (
    <PageContainer>
      <PageHeader title="Tasks" description="Work your agents proposed. Every task shows why it exists." />

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
            <div key={t.id} className="card flex items-start gap-3 p-4">
              <button
                onClick={() => update.mutate({ id: t.id, body: { status: t.status === "done" ? "todo" : "done" } })}
                className={`mt-0.5 grid h-5 w-5 shrink-0 place-items-center rounded border ${
                  t.status === "done" ? "border-emerald-500 bg-emerald-500 text-white" : "hover:border-accent"
                }`}
              >
                {t.status === "done" && <Check className="h-3.5 w-3.5" />}
              </button>
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <span className={`text-sm font-medium ${t.status === "done" ? "text-muted line-through" : ""}`}>
                    {t.title}
                  </span>
                  <PriorityBadge priority={t.priority} />
                  {t.requires_user_approval && !t.approved && (
                    <span className="rounded bg-amber-500/15 px-1.5 py-0.5 text-[11px] font-medium text-amber-500">
                      needs approval
                    </span>
                  )}
                </div>
                {t.description && <p className="mt-0.5 text-sm text-fg-subtle">{t.description}</p>}
                {t.rationale && <p className="mt-1 text-xs text-muted">Why: {t.rationale}</p>}
                <div className="mt-1.5 flex items-center gap-3 text-[11px] text-muted">
                  {t.originating_thought_id && (
                    <Link href={`/thoughts/${t.originating_thought_id}`} className="text-accent hover:underline">
                      originating thought →
                    </Link>
                  )}
                </div>
              </div>
              <StatusBadge status={t.status} />
            </div>
          ))}
        </div>
      ) : (
        <EmptyState icon={ListTodo} title="No tasks yet" description="Dispatch a thought and agents may propose tasks." />
      )}
    </PageContainer>
  );
}
