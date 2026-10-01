"use client";

import { LayoutGrid, Sparkles } from "lucide-react";
import { useState } from "react";

import { PageContainer, PageHeader } from "@/components/ui/page";
import { EmptyState, LoadingBlock } from "@/components/ui/states";
import { useGenerateReport, useReports } from "@/lib/hooks";
import { timeAgo } from "@/lib/utils";

const TYPES = [
  { key: "", label: "All" },
  { key: "morning", label: "Morning" },
  { key: "daily", label: "Daily" },
  { key: "weekly", label: "Weekly" },
  { key: "research", label: "Research" },
];

export default function ReportsPage() {
  const [type, setType] = useState("");
  const { data, isLoading } = useReports(type || undefined);
  const generate = useGenerateReport();
  const [open, setOpen] = useState<string | null>(null);

  return (
    <PageContainer>
      <PageHeader
        title="Reports"
        description="Chief of Staff synthesis — morning, daily and weekly."
        action={
          <div className="flex gap-2">
            {["morning", "daily", "weekly"].map((k) => (
              <button key={k} onClick={() => generate.mutate(k)} className="btn capitalize">
                <Sparkles className="h-3.5 w-3.5" /> {k}
              </button>
            ))}
          </div>
        }
      />

      <div className="mb-4 flex flex-wrap gap-1.5">
        {TYPES.map((t) => (
          <button key={t.key} onClick={() => setType(t.key)} className={`chip cursor-pointer ${type === t.key ? "border-accent bg-accent/10 text-fg" : ""}`}>
            {t.label}
          </button>
        ))}
      </div>

      {isLoading ? (
        <LoadingBlock />
      ) : data?.items.length ? (
        <div className="space-y-3">
          {data.items.map((r) => (
            <div key={r.id} className="card p-4">
              <button onClick={() => setOpen(open === r.id ? null : r.id)} className="flex w-full items-center justify-between text-left">
                <div>
                  <div className="font-medium">{r.title}</div>
                  <span className="text-[11px] text-muted">{r.type} · {timeAgo(r.created_at)}</span>
                </div>
                <span className="chip capitalize">{r.type}</span>
              </button>
              {open === r.id && <ReportContent content={r.content} />}
            </div>
          ))}
        </div>
      ) : (
        <EmptyState icon={LayoutGrid} title="No reports yet" description="Generate one above or let scheduled briefs run." />
      )}
    </PageContainer>
  );
}

function ReportContent({ content }: { content: Record<string, any> }) {
  return (
    <div className="mt-4 space-y-4 border-t pt-4">
      {content.headline && (
        <div className="grid grid-cols-3 gap-2 sm:grid-cols-6">
          {Object.entries(content.headline).map(([k, v]) => (
            <div key={k} className="rounded-md border bg-surface-2 p-2 text-center">
              <div className="text-lg font-semibold tabular-nums">{v as number}</div>
              <div className="text-[10px] text-muted">{k.replace(/_/g, " ")}</div>
            </div>
          ))}
        </div>
      )}
      {Object.entries(content)
        .filter(([k]) => k !== "headline" && Array.isArray(content[k]) && content[k].length)
        .map(([section, items]) => (
          <div key={section}>
            <div className="section-label mb-1.5">{section.replace(/_/g, " ")}</div>
            <ul className="space-y-1 text-sm text-fg-subtle">
              {(items as any[]).map((it, i) => (
                <li key={i}>• {it.label || it.topic || JSON.stringify(it)}</li>
              ))}
            </ul>
          </div>
        ))}
    </div>
  );
}
