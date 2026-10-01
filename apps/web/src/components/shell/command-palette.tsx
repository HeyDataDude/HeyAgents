"use client";

import {
  Boxes,
  FileText,
  LayoutGrid,
  ListTodo,
  Mic,
  Search as SearchIcon,
  Users,
} from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { useSearch } from "@/lib/hooks";
import { useUI } from "@/lib/store";

const COMMANDS = [
  { id: "talk", label: "Talk — new voice thought", icon: Mic, action: "talk" },
  { id: "thoughts", label: "Open Thoughts", icon: FileText, href: "/thoughts" },
  { id: "agents", label: "Open Agents", icon: Users, href: "/agents" },
  { id: "tasks", label: "Open Tasks", icon: ListTodo, href: "/tasks" },
  { id: "projects", label: "Open Projects", icon: Boxes, href: "/projects" },
  { id: "reports", label: "Generate / view Reports", icon: LayoutGrid, href: "/reports" },
  { id: "decisions", label: "View decisions (Inbox)", icon: SearchIcon, href: "/inbox" },
];

export function CommandPalette() {
  const { paletteOpen, togglePalette, openTalk } = useUI();
  const router = useRouter();
  const [q, setQ] = useState("");
  const { data: searchData } = useSearch(q);

  useEffect(() => {
    if (!paletteOpen) setQ("");
  }, [paletteOpen]);

  if (!paletteOpen) return null;

  const go = (href: string) => {
    router.push(href);
    togglePalette(false);
  };

  const filteredCommands = COMMANDS.filter((c) =>
    c.label.toLowerCase().includes(q.toLowerCase()),
  );
  const results = searchData?.results ?? [];

  return (
    <div
      className="fixed inset-0 z-[60] flex items-start justify-center bg-black/40 p-4 pt-[12vh] backdrop-blur-sm"
      onClick={() => togglePalette(false)}
    >
      <div
        className="card w-full max-w-lg overflow-hidden shadow-panel"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center gap-2 border-b px-4">
          <SearchIcon className="h-4 w-4 text-muted" />
          <input
            autoFocus
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Search thoughts, tasks, memory… or run a command"
            className="w-full bg-transparent py-3.5 text-sm outline-none placeholder:text-muted"
          />
          <kbd className="rounded border bg-surface-2 px-1.5 py-0.5 text-[10px] text-muted">esc</kbd>
        </div>

        <div className="max-h-[52vh] overflow-y-auto p-2">
          {q.length <= 1 || filteredCommands.length > 0 ? (
            <>
              <div className="px-2 py-1 text-[11px] font-semibold uppercase tracking-wider text-muted">
                Actions
              </div>
              {filteredCommands.map((c) => (
                <button
                  key={c.id}
                  onClick={() => (c.action === "talk" ? (openTalk(), togglePalette(false)) : go(c.href!))}
                  className="flex w-full items-center gap-3 rounded-md px-2 py-2 text-left text-sm hover:bg-surface-2"
                >
                  <c.icon className="h-4 w-4 text-fg-subtle" />
                  {c.label}
                </button>
              ))}
            </>
          ) : null}

          {results.length > 0 && (
            <>
              <div className="mt-2 px-2 py-1 text-[11px] font-semibold uppercase tracking-wider text-muted">
                Results
              </div>
              {results.map((r: any) => (
                <button
                  key={`${r.type}-${r.id}`}
                  onClick={() => go(resultHref(r))}
                  className="flex w-full items-start gap-3 rounded-md px-2 py-2 text-left hover:bg-surface-2"
                >
                  <span className="chip mt-0.5 shrink-0">{r.type}</span>
                  <span className="min-w-0">
                    <span className="block truncate text-sm">{r.title}</span>
                    {r.snippet && (
                      <span className="block truncate text-xs text-muted">{r.snippet}</span>
                    )}
                  </span>
                </button>
              ))}
            </>
          )}

          {q.length > 1 && results.length === 0 && filteredCommands.length === 0 && (
            <p className="px-2 py-6 text-center text-sm text-muted">No results for “{q}”.</p>
          )}
        </div>
      </div>
    </div>
  );
}

function resultHref(r: { type: string; id: string }): string {
  switch (r.type) {
    case "thought":
      return `/thoughts/${r.id}`;
    case "task":
      return `/tasks`;
    case "project":
      return `/projects/${r.id}`;
    case "research":
      return `/thoughts`;
    case "report":
      return `/reports`;
    default:
      return "/";
  }
}
