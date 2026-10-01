"use client";

import { Boxes, Plus } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import { StatusBadge } from "@/components/ui/badges";
import { PageContainer, PageHeader } from "@/components/ui/page";
import { EmptyState, LoadingBlock } from "@/components/ui/states";
import { api } from "@/lib/api";
import { useProjects } from "@/lib/hooks";

export default function ProjectsPage() {
  const { data, isLoading, refetch } = useProjects();
  const [creating, setCreating] = useState(false);
  const [name, setName] = useState("");

  const create = async () => {
    if (!name.trim()) return;
    await api.post("/api/projects", { name });
    setName("");
    setCreating(false);
    refetch();
  };

  return (
    <PageContainer>
      <PageHeader
        title="Projects"
        description="Living workspaces that aggregate thoughts, tasks, research and decisions."
        action={
          <button onClick={() => setCreating((v) => !v)} className="btn btn-primary">
            <Plus className="h-4 w-4" /> New project
          </button>
        }
      />

      {creating && (
        <div className="card mb-4 flex gap-2 p-3">
          <input autoFocus value={name} onChange={(e) => setName(e.target.value)} placeholder="Project name" className="input h-9" />
          <button onClick={create} className="btn btn-primary h-9 shrink-0">Create</button>
        </div>
      )}

      {isLoading ? (
        <LoadingBlock />
      ) : data?.items.length ? (
        <div className="grid gap-3 sm:grid-cols-2">
          {data.items.map((p) => (
            <Link key={p.id} href={`/projects/${p.id}`} className="card p-4 hover:bg-surface-2">
              <div className="mb-1 flex items-center justify-between">
                <span className="font-medium">{p.name}</span>
                <StatusBadge status={p.status} />
              </div>
              <p className="line-clamp-2 text-sm text-muted">{p.description || "No description"}</p>
              <div className="mt-3 flex gap-3 text-[11px] text-muted">
                <span>{p.related_thought_ids.length} thoughts</span>
                <span>{p.related_task_ids.length} tasks</span>
              </div>
            </Link>
          ))}
        </div>
      ) : (
        <EmptyState icon={Boxes} title="No projects yet" description="Create one, or let the Builder agent propose projects from your ideas." />
      )}
    </PageContainer>
  );
}
