"use client";

import { ArrowRight, Lightbulb, Mic, Sparkles } from "lucide-react";
import Link from "next/link";

import { StatusBadge } from "@/components/ui/badges";
import { EmptyState, LoadingBlock } from "@/components/ui/states";
import { useHome } from "@/lib/hooks";
import { useUI } from "@/lib/store";

export default function HomePage() {
  const { data, isLoading } = useHome();
  const openTalk = useUI((s) => s.openTalk);

  return (
    <div className="mx-auto max-w-4xl p-6 lg:p-8">
      {/* Hero Talk */}
      <button
        onClick={openTalk}
        className="group mb-8 flex w-full flex-col items-center gap-3 rounded-xl border bg-surface py-10 shadow-soft transition-colors hover:bg-surface-2"
      >
        <span className="recording-pulse grid h-16 w-16 place-items-center rounded-full bg-accent text-accent-fg transition-transform group-hover:scale-105">
          <Mic className="h-7 w-7" />
        </span>
        <span className="text-lg font-semibold">What are you thinking?</span>
        <span className="text-sm text-muted">Press <kbd className="rounded border bg-surface-2 px-1.5">T</kbd> or tap to talk</span>
      </button>

      {isLoading ? (
        <LoadingBlock />
      ) : (
        <>
          {/* Today stats */}
          <div className="mb-8">
            <h2 className="section-label mb-3">Today</h2>
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              <Stat value={data?.today.thoughts_captured ?? 0} label="thoughts captured" />
              <Stat value={data?.today.active_investigations ?? 0} label="active investigations" />
              <Stat value={data?.today.decisions_waiting ?? 0} label="decisions waiting" accent />
              <Stat value={data?.today.tasks_generated ?? 0} label="tasks generated" />
            </div>
          </div>

          {/* Needs attention */}
          <div className="mb-8">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="section-label">Needs your attention</h2>
              <Link href="/inbox" className="text-xs text-accent hover:underline">
                Open inbox
              </Link>
            </div>
            {data?.needs_attention.length ? (
              <div className="space-y-2">
                {data.needs_attention.map((item) => (
                  <Link
                    key={item.id}
                    href={item.thought_id ? `/thoughts/${item.thought_id}` : "/inbox"}
                    className="card flex items-center gap-3 px-4 py-3 transition-colors hover:bg-surface-2"
                  >
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium">{item.agent}</span>
                        <StatusBadge status={item.status} />
                      </div>
                      <p className="truncate text-sm text-fg-subtle">{item.summary}</p>
                    </div>
                    <ArrowRight className="h-4 w-4 shrink-0 text-muted" />
                  </Link>
                ))}
              </div>
            ) : (
              <EmptyState
                icon={Sparkles}
                title="Nothing needs you right now"
                description="When agents finish work or need a decision, it shows up here."
              />
            )}
          </div>

          {/* Today's connection */}
          {data?.todays_connection && (
            <div>
              <h2 className="section-label mb-3">Today&apos;s connection</h2>
              <div className="card border-accent/30 bg-accent/5 p-5">
                <div className="mb-2 flex items-center gap-2">
                  <Lightbulb className="h-4 w-4 text-accent" />
                  <span className="text-sm font-semibold">{data.todays_connection.title}</span>
                </div>
                <p className="text-sm text-fg-subtle">{data.todays_connection.explanation}</p>
                <div className="mt-3 flex flex-wrap gap-1.5">
                  {data.todays_connection.related_objects.map((o) => (
                    <Link
                      key={o.id}
                      href={o.type === "thought" ? `/thoughts/${o.id}` : "#"}
                      className="chip hover:bg-surface"
                    >
                      {o.label || o.id}
                    </Link>
                  ))}
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}

function Stat({ value, label, accent }: { value: number; label: string; accent?: boolean }) {
  return (
    <div className="card p-4">
      <div className={`text-2xl font-semibold tabular-nums ${accent && value > 0 ? "text-accent" : ""}`}>
        {value}
      </div>
      <div className="mt-0.5 text-xs text-muted">{label}</div>
    </div>
  );
}
