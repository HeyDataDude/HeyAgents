import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function timeAgo(iso: string): string {
  const then = new Date(iso).getTime();
  const diff = Date.now() - then;
  const s = Math.round(diff / 1000);
  if (s < 60) return "just now";
  const m = Math.round(s / 60);
  if (m < 60) return `${m}m ago`;
  const h = Math.round(m / 60);
  if (h < 24) return `${h}h ago`;
  const d = Math.round(h / 24);
  if (d < 7) return `${d}d ago`;
  return new Date(iso).toLocaleDateString();
}

export function formatDuration(seconds?: number | null): string {
  if (!seconds) return "0:00";
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

const ACCENTS: Record<string, string> = {
  blue: "bg-blue-500/15 text-blue-600 dark:text-blue-400",
  violet: "bg-violet-500/15 text-violet-600 dark:text-violet-400",
  amber: "bg-amber-500/15 text-amber-600 dark:text-amber-400",
  emerald: "bg-emerald-500/15 text-emerald-600 dark:text-emerald-400",
  cyan: "bg-cyan-500/15 text-cyan-600 dark:text-cyan-400",
  orange: "bg-orange-500/15 text-orange-600 dark:text-orange-400",
  rose: "bg-rose-500/15 text-rose-600 dark:text-rose-400",
  slate: "bg-slate-500/15 text-slate-600 dark:text-slate-300",
};
export function accentClass(accent: string): string {
  return ACCENTS[accent] || ACCENTS.slate;
}

export function confidenceColor(c: number): string {
  if (c >= 0.8) return "text-emerald-500";
  if (c >= 0.5) return "text-amber-500";
  return "text-muted";
}
