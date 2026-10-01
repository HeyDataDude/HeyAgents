"use client";

import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import type {
  ActivityItem,
  Agent,
  Connection,
  HomeData,
  InboxItem,
  Memory,
  Project,
  Report,
  ResearchJob,
  Task,
  Thought,
} from "@/types";
import { api } from "./api";

// ── Home ────────────────────────────────────────────────────────────────────
export const useHome = () =>
  useQuery({ queryKey: ["home"], queryFn: () => api.get<HomeData>("/api/home"), refetchInterval: 8000 });

// ── Thoughts ──────────────────────────────────────────────────────────────────
export const useThoughts = (params: Record<string, string> = {}) => {
  const qs = new URLSearchParams(params).toString();
  return useQuery({
    queryKey: ["thoughts", params],
    queryFn: () => api.get<{ items: Thought[]; total: number }>(`/api/thoughts?${qs}`),
  });
};

export const useThoughtDetail = (id: string) =>
  useQuery({
    queryKey: ["thought-detail", id],
    queryFn: () => api.get<any>(`/api/thoughts/${id}/detail`),
    enabled: !!id,
  });

export const useCreateTextThought = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: { text: string; title?: string }) =>
      api.post<Thought>("/api/thoughts/text", body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["thoughts"] }),
  });
};

export const useUploadAudioThought = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (form: FormData) => api.upload<Thought>("/api/thoughts/audio", form),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["thoughts"] });
      qc.invalidateQueries({ queryKey: ["home"] });
    },
  });
};

export const useDispatchThought = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: any }) =>
      api.post<{ dispatch_id: string; status: string }>(`/api/thoughts/${id}/dispatch`, body),
    onSuccess: (_d, v) => {
      qc.invalidateQueries({ queryKey: ["thought-detail", v.id] });
      qc.invalidateQueries({ queryKey: ["home"] });
      qc.invalidateQueries({ queryKey: ["inbox"] });
    },
  });
};

// ── Agents ────────────────────────────────────────────────────────────────────
export const useAgents = () =>
  useQuery({ queryKey: ["agents"], queryFn: () => api.get<{ items: Agent[] }>("/api/agents") });

export const useAgentOverview = (id: string) =>
  useQuery({ queryKey: ["agent-overview", id], queryFn: () => api.get<any>(`/api/agents/${id}/overview`), enabled: !!id });

export const useAgentInbox = (id: string) =>
  useQuery({ queryKey: ["agent-inbox", id], queryFn: () => api.get<any>(`/api/agents/${id}/inbox`), enabled: !!id });

export const useAgentMemory = (id: string) =>
  useQuery({ queryKey: ["agent-memory", id], queryFn: () => api.get<{ items: any[] }>(`/api/agents/${id}/memory`), enabled: !!id });

// ── Inbox / Tasks / Projects / Reports / Research / Memory / Activity ───────────
export const useInbox = (filter = "all") =>
  useQuery({ queryKey: ["inbox", filter], queryFn: () => api.get<{ items: InboxItem[] }>(`/api/inbox?filter=${filter}`), refetchInterval: 10000 });

export const useAnswerQuestion = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, answer }: { id: string; answer: string }) =>
      api.post(`/api/inbox/questions/${id}/answer`, { answer }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["inbox"] });
      qc.invalidateQueries({ queryKey: ["home"] });
    },
  });
};

export const useTasks = (params: Record<string, string> = {}) => {
  const qs = new URLSearchParams(params).toString();
  return useQuery({ queryKey: ["tasks", params], queryFn: () => api.get<{ items: Task[] }>(`/api/tasks?${qs}`) });
};

export const useUpdateTask = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: any }) => api.patch<Task>(`/api/tasks/${id}`, body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["tasks"] }),
  });
};

export const useProjects = () =>
  useQuery({ queryKey: ["projects"], queryFn: () => api.get<{ items: Project[] }>("/api/projects") });

export const useReports = (type?: string) =>
  useQuery({ queryKey: ["reports", type], queryFn: () => api.get<{ items: Report[] }>(`/api/reports${type ? `?type=${type}` : ""}`) });

export const useGenerateReport = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (kind: string) => api.post<Report>(`/api/reports/generate?kind=${kind}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["reports"] }),
  });
};

export const useResearch = () =>
  useQuery({ queryKey: ["research"], queryFn: () => api.get<{ items: ResearchJob[] }>("/api/research"), refetchInterval: 6000 });

export const useMemoryTree = () =>
  useQuery({ queryKey: ["memory-tree"], queryFn: () => api.get<any>("/api/memory/tree") });

export const useMemory = (params: Record<string, string> = {}) => {
  const qs = new URLSearchParams(params).toString();
  return useQuery({ queryKey: ["memory", params], queryFn: () => api.get<{ items: Memory[] }>(`/api/memory?${qs}`) });
};

export const useActivity = () =>
  useQuery({ queryKey: ["activity"], queryFn: () => api.get<{ items: ActivityItem[] }>("/api/activity"), refetchInterval: 8000 });

export const useConnections = () =>
  useQuery({ queryKey: ["connections"], queryFn: () => api.get<{ items: Connection[] }>("/api/activity/connections") });

export const useSearch = (q: string) =>
  useQuery({ queryKey: ["search", q], queryFn: () => api.get<any>(`/api/search?q=${encodeURIComponent(q)}`), enabled: q.length > 1 });

export const useDiagnostics = () =>
  useQuery({ queryKey: ["diagnostics"], queryFn: () => api.get<any>("/api/system/diagnostics"), refetchInterval: 10000 });

export const useJobs = () =>
  useQuery({ queryKey: ["jobs"], queryFn: () => api.get<any>("/api/jobs"), refetchInterval: 5000 });
