"use client";

import { Activity, CheckCircle2, XCircle } from "lucide-react";

import { AgentIcon } from "@/components/ui/agent-icon";
import { PageContainer, PageHeader } from "@/components/ui/page";
import { LoadingBlock } from "@/components/ui/states";
import { api } from "@/lib/api";
import { useAgents, useDiagnostics, useJobs } from "@/lib/hooks";
import { useQueryClient } from "@tanstack/react-query";
import { AUTONOMY_LABELS } from "@/types";

export default function SettingsPage() {
  const { data: diag, isLoading } = useDiagnostics();
  const { data: agents } = useAgents();
  const { data: jobs } = useJobs();
  const qc = useQueryClient();

  const updateAgent = async (id: string, body: any) => {
    await api.patch(`/api/agents/${id}`, body);
    qc.invalidateQueries({ queryKey: ["agents"] });
  };

  return (
    <PageContainer>
      <PageHeader title="Settings" description="Agents, autonomy, providers and system diagnostics." />

      {/* Diagnostics */}
      <section className="card mb-6 p-4">
        <h3 className="section-label mb-3">System diagnostics</h3>
        {isLoading ? (
          <LoadingBlock />
        ) : (
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <Health label="Database" ok={diag?.database?.ok} detail={`${diag?.database?.thoughts ?? 0} thoughts`} />
            <Health label="Redis / queue" ok={diag?.redis?.ok} detail={`${diag?.queue?.pending_jobs ?? 0} pending`} />
            <Health label="Provider mode" ok detail={diag?.provider_mode} />
            <Health label="Storage" ok detail={diag?.storage_backend} />
          </div>
        )}
        {diag?.providers && (
          <div className="mt-3 flex flex-wrap gap-1.5">
            {Object.entries(diag.providers).map(([k, v]) => (
              <span key={k} className="chip">{k}: {v as string}</span>
            ))}
          </div>
        )}
      </section>

      {/* Agents config */}
      <section className="card mb-6 p-4">
        <h3 className="section-label mb-3">Agents</h3>
        <div className="space-y-2">
          {(agents?.items ?? []).map((a) => (
            <div key={a.id} className="flex items-center gap-3 rounded-md border p-3">
              <AgentIcon icon={a.icon} accent={a.accent} size="sm" />
              <div className="min-w-0 flex-1">
                <div className="text-sm font-medium">{a.name}</div>
                <div className="text-[11px] text-muted">{a.model}</div>
              </div>
              <select
                value={a.autonomy_level}
                onChange={(e) => updateAgent(a.id, { autonomy_level: Number(e.target.value) })}
                className="rounded-md border bg-surface px-2 py-1 text-xs"
              >
                {Object.entries(AUTONOMY_LABELS).map(([k, label]) => (
                  <option key={k} value={k}>{label}</option>
                ))}
              </select>
              <label className="flex items-center gap-1.5 text-xs">
                <input
                  type="checkbox"
                  checked={a.enabled}
                  onChange={(e) => updateAgent(a.id, { enabled: e.target.checked })}
                />
                Enabled
              </label>
            </div>
          ))}
        </div>
      </section>

      {/* Jobs */}
      <section className="card p-4">
        <h3 className="section-label mb-3">Background jobs</h3>
        {jobs?.items?.length ? (
          <div className="space-y-1.5">
            {jobs.items.slice(0, 10).map((j: any) => (
              <div key={j.id} className="flex items-center justify-between rounded-md border px-3 py-2 text-sm">
                <span className="font-mono text-xs">{j.kind}</span>
                <div className="flex items-center gap-2">
                  <span className="text-[11px] text-muted">{j.progress}%</span>
                  <span className="chip capitalize">{j.status}</span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-muted">No jobs.</p>
        )}
      </section>
    </PageContainer>
  );
}

function Health({ label, ok, detail }: { label: string; ok?: boolean; detail?: string }) {
  return (
    <div className="rounded-md border p-3">
      <div className="flex items-center gap-2">
        {ok ? <CheckCircle2 className="h-4 w-4 text-emerald-500" /> : <XCircle className="h-4 w-4 text-red-500" />}
        <span className="text-sm font-medium">{label}</span>
      </div>
      <div className="mt-1 text-xs text-muted">{detail}</div>
    </div>
  );
}
