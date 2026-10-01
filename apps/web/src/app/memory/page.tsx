"use client";

import { Brain, Trash2 } from "lucide-react";
import { useState } from "react";

import { PageContainer, PageHeader } from "@/components/ui/page";
import { EmptyState, LoadingBlock } from "@/components/ui/states";
import { api } from "@/lib/api";
import { useMemory, useMemoryTree } from "@/lib/hooks";
import { useQueryClient } from "@tanstack/react-query";
import { timeAgo } from "@/lib/utils";

export default function MemoryPage() {
  const { data: tree, isLoading } = useMemoryTree();
  const [scope, setScope] = useState("global");
  const [agentId, setAgentId] = useState<string | undefined>();
  const params: Record<string, string> = { scope };
  if (agentId) params.agent_id = agentId;
  const { data: mem } = useMemory(params);
  const qc = useQueryClient();

  const del = async (id: string) => {
    await api.del(`/api/memory/${id}`);
    qc.invalidateQueries({ queryKey: ["memory"] });
    qc.invalidateQueries({ queryKey: ["memory-tree"] });
  };

  return (
    <PageContainer>
      <PageHeader title="Memory Explorer" description="Nothing is hidden. Inspect, trace provenance, edit or delete." />

      {isLoading ? (
        <LoadingBlock />
      ) : (
        <div className="grid gap-6 lg:grid-cols-[220px_1fr]">
          <nav className="space-y-4">
            <div>
              <div className="section-label mb-2">Global</div>
              <button
                onClick={() => { setScope("global"); setAgentId(undefined); }}
                className={`nav-link w-full ${scope === "global" ? "nav-link-active" : ""}`}
              >
                <Brain className="h-4 w-4" /> All global
                <span className="ml-auto text-xs text-muted">
                  {(tree?.global ?? []).reduce((a: number, c: any) => a + c.count, 0)}
                </span>
              </button>
            </div>
            <div>
              <div className="section-label mb-2">Agents</div>
              {(tree?.agents ?? []).map((a: any) => (
                <button
                  key={a.agent_id}
                  onClick={() => { setScope("agent"); setAgentId(a.agent_id); }}
                  className={`nav-link w-full ${agentId === a.agent_id ? "nav-link-active" : ""}`}
                >
                  {a.agent_name}
                  <span className="ml-auto text-xs text-muted">{a.count}</span>
                </button>
              ))}
            </div>
          </nav>

          <div>
            {mem?.items.length ? (
              <div className="space-y-2">
                {mem.items.map((m) => (
                  <div key={m.id} className="card group flex items-start justify-between gap-3 p-4">
                    <div className="min-w-0">
                      <div className="mb-1 flex items-center gap-2">
                        <span className="chip">{m.category}</span>
                        <span className="text-[11px] text-muted">{timeAgo(m.created_at)}</span>
                      </div>
                      <p className="text-sm">{m.content}</p>
                      {m.originating_thought_id && (
                        <a href={`/thoughts/${m.originating_thought_id}`} className="mt-1 inline-block text-[11px] text-accent hover:underline">
                          provenance: originating thought →
                        </a>
                      )}
                    </div>
                    <button onClick={() => del(m.id)} className="btn h-8 w-8 shrink-0 p-0 opacity-0 group-hover:opacity-100" aria-label="Delete">
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  </div>
                ))}
              </div>
            ) : (
              <EmptyState icon={Brain} title="No memory in this scope" />
            )}
          </div>
        </div>
      )}
    </PageContainer>
  );
}
