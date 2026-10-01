"use client";

import { cn } from "@/lib/utils";

const STATUS_STYLES: Record<string, string> = {
  completed: "bg-emerald-500/15 text-emerald-500",
  done: "bg-emerald-500/15 text-emerald-500",
  processing: "bg-blue-500/15 text-blue-500",
  researching: "bg-blue-500/15 text-blue-500",
  working: "bg-blue-500/15 text-blue-500",
  queued: "bg-slate-500/15 text-slate-400",
  todo: "bg-slate-500/15 text-slate-400",
  waiting_for_user: "bg-amber-500/15 text-amber-500",
  needs_decision: "bg-amber-500/15 text-amber-500",
  failed: "bg-red-500/15 text-red-500",
  partial: "bg-amber-500/15 text-amber-500",
  dispatched: "bg-violet-500/15 text-violet-500",
  ready_for_review: "bg-cyan-500/15 text-cyan-500",
  in_progress: "bg-blue-500/15 text-blue-500",
  idle: "bg-slate-500/10 text-muted",
};

const PRIORITY_STYLES: Record<string, string> = {
  urgent: "bg-red-500/15 text-red-500",
  high: "bg-orange-500/15 text-orange-500",
  medium: "bg-slate-500/15 text-slate-400",
  low: "bg-slate-500/10 text-muted",
};

export function StatusBadge({ status }: { status: string }) {
  return (
    <span className={cn("rounded px-1.5 py-0.5 text-[11px] font-medium capitalize", STATUS_STYLES[status] ?? "bg-surface-2 text-fg-subtle")}>
      {status.replace(/_/g, " ")}
    </span>
  );
}

export function PriorityBadge({ priority }: { priority: string }) {
  return (
    <span className={cn("rounded px-1.5 py-0.5 text-[11px] font-medium capitalize", PRIORITY_STYLES[priority] ?? "bg-surface-2")}>
      {priority}
    </span>
  );
}
