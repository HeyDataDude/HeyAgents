"use client";

import {
  Activity,
  Compass,
  Film,
  Hammer,
  Microscope,
  Network,
  PenLine,
  Sparkles,
  TrendingUp,
} from "lucide-react";

import { accentClass, cn } from "@/lib/utils";

const ICONS: Record<string, React.ComponentType<{ className?: string }>> = {
  microscope: Microscope,
  "pen-line": PenLine,
  film: Film,
  activity: Activity,
  network: Network,
  hammer: Hammer,
  "trending-up": TrendingUp,
  compass: Compass,
  sparkles: Sparkles,
};

export function AgentIcon({
  icon,
  accent,
  size = "md",
}: {
  icon: string;
  accent: string;
  size?: "sm" | "md" | "lg";
}) {
  const Icon = ICONS[icon] ?? Sparkles;
  const dims = size === "lg" ? "h-10 w-10" : size === "sm" ? "h-6 w-6" : "h-8 w-8";
  const iconDims = size === "lg" ? "h-5 w-5" : size === "sm" ? "h-3.5 w-3.5" : "h-4 w-4";
  return (
    <span className={cn("grid shrink-0 place-items-center rounded-md", dims, accentClass(accent))}>
      <Icon className={iconDims} />
    </span>
  );
}
