"use client";

import { ArrowLeft, Mic } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";

import { AgentChat } from "@/components/agent/agent-chat";
import { AgentIcon } from "@/components/ui/agent-icon";
import { StatusBadge } from "@/components/ui/badges";
import { PageContainer } from "@/components/ui/page";
import { EmptyState, LoadingBlock } from "@/components/ui/states";
import { api } from "@/lib/api";
import { useAgentInbox, useAgentMemory, useAgentOverview } from "@/lib/hooks";
import { AUTONOMY_LABELS } from "@/types";
import { timeAgo } from "@/lib/utils";

const TABS = ["Overview", "Chat", "Inbox", "Memory", "Tasks", "Activity"] as const;
type Tab = (typeof TABS)[number];

export default function AgentWorkspace() {
  const { id } = useParams<{ id: string }>();
  const [tab, setTab] = useState<Tab>("Overview");
  const { data, isLoading } = useAgentOverview(id);

  if (isLoading || !data) return <PageContainer><LoadingBlock /></PageContainer>;
  const agent = data.agent;

  const startVoice = async () => {
    const session = await api.post<any>("/api/voice/session", { agent_id: agent.id });
    alert(
      `Realtime voice session created (provider: ${session.provider}).\nRoom: ${session.room}\n\n` +
        "In mock mode this returns a demo token. With COUNCIL_REALTIME_PROVIDER=livekit it mints a real LiveKit token.",
    );
  };

  return (
    <PageContainer>
      <Link href="/agents" className="mb-4 inline-flex items-center gap-1.5 text-sm text-muted hover:text-fg">
        <ArrowLeft className="h-4 w-4" /> Agents
      </Link>

      <div className="mb-5 flex items-start gap-3">
        <AgentIcon icon={agent.icon} accent={agent.accent} size="lg" />
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-semibold tracking-tight">{agent.name}</h1>
            <StatusBadge status={data.status} />
          </div>
          <p className="mt-0.5 max-w-2xl text-sm text-muted">{agent.description}</p>
          <div className="mt-2 flex flex-wrap gap-1.5 text-[11px]">
            <span className="chip">Autonomy: {AUTONOMY_LABELS[agent.autonomy_level]}</span>
            <span className="chip">Model: {agent.model}</span>
            <span className="chip capitalize">Interrupt: {agent.interruption_policy.replace(/_/g, " ")}</span>
          </div>
        </div>
        <button onClick={startVoice} className="btn">
          <Mic className="h-4 w-4" /> Talk
        </button>
      </div>

      <div className="mb-5 flex gap-1 overflow-x-auto border-b">
        {TABS.map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`-mb-px border-b-2 px-3 py-2 text-sm font-medium transition-colors ${
              tab === t ? "border-accent text-fg" : "border-transparent text-muted hover:text-fg"
            }`}
          >
            {t}
          </button>
        ))}
      </div>

      {tab === "Overview" && <Overview data={data} />}
      {tab === "Chat" && <AgentChat agentId={agent.id} agentName={agent.name} />}
      {tab === "Inbox" && <AgentInboxTab agentId={id} />}
      {tab === "Memory" && <AgentMemoryTab agentId={id} />}
      {tab === "Tasks" && <TaskList tasks={data.tasks} />}
      {tab === "Activity" && <ResearchList research={data.research_jobs} />}
    </PageContainer>
  );
}

function Overview({ data }: { data: any }) {
  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <section className="card p-4">
        <h3 className="section-label mb-2.5">Recent memory</h3>
        {data.recent_memory.length ? (
          <ul className="space-y-2 text-sm">
            {data.recent_memory.map((m: any) => (
              <li key={m.id}>
                <span className="chip mr-2">{m.category}</span>
                {m.content}
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-sm text-muted">No memory yet.</p>
        )}
      </section>
      <section className="card p-4">
        <h3 className="section-label mb-2.5">Open work</h3>
        <TaskList tasks={data.tasks} compact />
      </section>
    </div>
  );
}

function AgentInboxTab({ agentId }: { agentId: string }) {
  const { data, isLoading } = useAgentInbox(agentId);
  if (isLoading) return <LoadingBlock />;
  if (!data?.items.length) return <EmptyState title="Inbox empty" description="Thoughts dispatched to this agent appear here." />;
  return (
    <div className="space-y-2">
      {data.items.map((d: any) => (
        <Link key={d.id} href={`/thoughts/${d.thought_id}`} className="card flex items-center justify-between gap-3 px-4 py-3 hover:bg-surface-2">
          <div className="min-w-0">
            <p className="truncate text-sm">{d.response_summary || "Processing…"}</p>
            <span className="text-[11px] text-muted">{d.response_mode} · {timeAgo(d.created_at)}</span>
          </div>
          <StatusBadge status={d.status} />
        </Link>
      ))}
    </div>
  );
}

function AgentMemoryTab({ agentId }: { agentId: string }) {
  const { data, isLoading } = useAgentMemory(agentId);
  if (isLoading) return <LoadingBlock />;
  if (!data?.items.length) return <EmptyState title="No memory yet" description="This agent hasn't recorded anything." />;
  return (
    <div className="space-y-2">
      {data.items.map((m: any) => (
        <div key={m.id} className="card px-4 py-3">
          <div className="mb-1 flex items-center justify-between">
            <span className="chip">{m.category}</span>
            <span className="text-[11px] text-muted">{timeAgo(m.created_at)}</span>
          </div>
          <p className="text-sm">{m.content}</p>
          {m.originating_thought_id && (
            <Link href={`/thoughts/${m.originating_thought_id}`} className="mt-1 inline-block text-[11px] text-accent hover:underline">
              from originating thought →
            </Link>
          )}
        </div>
      ))}
    </div>
  );
}

function TaskList({ tasks, compact }: { tasks: any[]; compact?: boolean }) {
  if (!tasks.length) return <p className="text-sm text-muted">No tasks.</p>;
  return (
    <div className="space-y-2">
      {tasks.map((t) => (
        <div key={t.id} className="flex items-center justify-between rounded-md border px-3 py-2 text-sm">
          <span className="truncate">{t.title}</span>
          <StatusBadge status={t.status} />
        </div>
      ))}
    </div>
  );
}

function ResearchList({ research }: { research: any[] }) {
  if (!research.length) return <EmptyState title="No research jobs" />;
  return (
    <div className="space-y-2">
      {research.map((r) => (
        <div key={r.id} className="card px-4 py-3">
          <div className="flex items-center justify-between">
            <span className="truncate text-sm">{r.question}</span>
            <StatusBadge status={r.status} />
          </div>
        </div>
      ))}
    </div>
  );
}
