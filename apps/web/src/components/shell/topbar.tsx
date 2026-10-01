"use client";

import { Moon, Search, Sun } from "lucide-react";
import { useTheme } from "next-themes";
import { useEffect, useState } from "react";

import { useUI } from "@/lib/store";

export function Topbar({ title }: { title?: string }) {
  const togglePalette = useUI((s) => s.togglePalette);
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);

  return (
    <header className="flex h-14 shrink-0 items-center justify-between border-b bg-surface/80 px-5 backdrop-blur">
      <h1 className="text-sm font-semibold tracking-tight text-fg-subtle">{title}</h1>
      <div className="flex items-center gap-2">
        <button
          onClick={() => togglePalette(true)}
          className="btn h-8 gap-2 text-xs text-fg-subtle"
          aria-label="Open command palette"
        >
          <Search className="h-3.5 w-3.5" />
          <span className="hidden sm:inline">Search</span>
          <kbd className="rounded border bg-surface-2 px-1 py-0.5 text-[10px]">⌘K</kbd>
        </button>
        {mounted && (
          <button
            onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
            className="btn h-8 w-8 p-0"
            aria-label="Toggle theme"
          >
            {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
          </button>
        )}
      </div>
    </header>
  );
}
