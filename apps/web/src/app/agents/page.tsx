"use client";

import Link from "next/link";

import { AgentIcon } from "@/components/ui/agent-icon";
import { StatusBadge } from "@/components/ui/badges";
import { PageContainer, PageHeader } from "@/components/ui/page";
import { LoadingBlock } from "@/components/ui/states";
import { useAgents } from "@/lib/hooks";
import { AUTONOMY_LABELS } from "@/types";

export default function AgentsPage() {
  const { data, isLoading } = useAgents();
  if (isLoading) return <PageContainer><LoadingBlock /></PageContainer>;

  const agents = data?.items ?? [];
  const specialists = agents.filter((a) => !a.is_supervisor);
  const supervisors = agents.filter((a) => a.is_supervisor);

  return (
    <PageContainer>
      <PageHeader title="Agents" description="Your persistent specialists. Each has its own memory, inbox and workspace." />

      {supervisors.length > 0 && (
        <>
          <h2 className="section-label mb-2">Supervisor</h2>
          <div className="mb-6 grid gap-3 sm:grid-cols-2">
            {supervisors.map((a) => <AgentCard key={a.id} agent={a} />)}
          </div>
        </>
      )}

      <h2 className="section-label mb-2">Specialists</h2>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {specialists.map((a) => <AgentCard key={a.id} agent={a} />)}
      </div>
    </PageContainer>
  );
}

function AgentCard({ agent }: { agent: any }) {
  return (
    <Link href={`/agents/${agent.id}`} className="card p-4 transition-colors hover:bg-surface-2">
      <div className="mb-2 flex items-start justify-between">
        <AgentIcon icon={agent.icon} accent={agent.accent} size="md" />
        <StatusBadge status={agent.status ?? "idle"} />
      </div>
      <div className="font-medium">{agent.name}</div>
      <p className="mt-1 line-clamp-2 text-xs text-muted">{agent.description}</p>
      <div className="mt-3 flex items-center justify-between text-[11px] text-muted">
        <span>{AUTONOMY_LABELS[agent.autonomy_level]}</span>
        <div className="flex gap-2">
          {agent.active_work_count ? <span>{agent.active_work_count} active</span> : null}
          {agent.unread_count ? <span className="text-accent">{agent.unread_count} unread</span> : null}
        </div>
      </div>
    </Link>
  );
}
