"use client";

import { ArrowLeft } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";

import { StatusBadge } from "@/components/ui/badges";
import { PageContainer } from "@/components/ui/page";
import { LoadingBlock } from "@/components/ui/states";
import { api } from "@/lib/api";

export default function ProjectDetail() {
  const { id } = useParams<{ id: string }>();
  const { data, isLoading } = useQuery({
    queryKey: ["project", id],
    queryFn: () => api.get<any>(`/api/projects/${id}`),
  });

  if (isLoading || !data) return <PageContainer><LoadingBlock /></PageContainer>;
  const p = data.project;

  return (
    <PageContainer>
      <Link href="/projects" className="mb-4 inline-flex items-center gap-1.5 text-sm text-muted hover:text-fg">
        <ArrowLeft className="h-4 w-4" /> Projects
      </Link>
      <div className="mb-1 flex items-center gap-2">
        <h1 className="text-xl font-semibold tracking-tight">{p.name}</h1>
        <StatusBadge status={p.status} />
      </div>
      <p className="mb-6 text-sm text-muted">{p.description || "No description"}</p>

      <div className="grid gap-4 lg:grid-cols-3">
        <Section title="Tasks">
          {data.tasks.length ? data.tasks.map((t: any) => (
            <Row key={t.id} label={t.title} badge={t.status} />
          )) : <Empty />}
        </Section>
        <Section title="Thoughts">
          {data.thoughts.length ? data.thoughts.map((t: any) => (
            <Link key={t.id} href={`/thoughts/${t.id}`} className="block py-1.5 text-sm hover:text-accent">{t.title}</Link>
          )) : <Empty />}
        </Section>
        <Section title="Research">
          {data.research_jobs.length ? data.research_jobs.map((r: any) => (
            <Row key={r.id} label={r.question} badge={r.status} />
          )) : <Empty />}
        </Section>
      </div>
    </PageContainer>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="card p-4">
      <h3 className="section-label mb-2.5">{title}</h3>
      {children}
    </section>
  );
}
function Row({ label, badge }: { label: string; badge: string }) {
  return (
    <div className="flex items-center justify-between py-1.5 text-sm">
      <span className="truncate">{label}</span>
      <StatusBadge status={badge} />
    </div>
  );
}
function Empty() {
  return <p className="text-sm text-muted">Nothing yet.</p>;
}
