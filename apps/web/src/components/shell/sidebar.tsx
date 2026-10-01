"use client";

import {
  Activity,
  Boxes,
  Brain,
  FileText,
  Home,
  Inbox,
  LayoutGrid,
  ListTodo,
  Mic,
  Search,
  Settings,
  Users,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { cn } from "@/lib/utils";
import { useInbox } from "@/lib/hooks";
import { useUI } from "@/lib/store";

const NAV = [
  { href: "/thoughts", label: "Thoughts", icon: FileText },
  { href: "/agents", label: "Agents", icon: Users },
  { href: "/tasks", label: "Tasks", icon: ListTodo },
  { href: "/projects", label: "Projects", icon: Boxes },
  { href: "/reports", label: "Reports", icon: LayoutGrid },
  { href: "/memory", label: "Memory", icon: Brain },
  { href: "/activity", label: "Activity", icon: Activity },
];

export function Sidebar() {
  const pathname = usePathname();
  const openTalk = useUI((s) => s.openTalk);
  const togglePalette = useUI((s) => s.togglePalette);
  const { data: inbox } = useInbox("all");
  const inboxCount = inbox?.items.length ?? 0;

  const isActive = (href: string) =>
    href === "/" ? pathname === "/" : pathname.startsWith(href);

  return (
    <aside className="flex h-full w-60 shrink-0 flex-col border-r bg-surface">
      <div className="flex h-14 items-center gap-2 px-4">
        <div className="grid h-7 w-7 place-items-center rounded-md bg-accent text-accent-fg">
          <Boxes className="h-4 w-4" />
        </div>
        <span className="text-[15px] font-semibold tracking-tight">Council</span>
      </div>

      <div className="px-3 pb-2">
        <button onClick={openTalk} className="btn btn-primary w-full justify-start gap-2.5 py-2">
          <Mic className="h-4 w-4" />
          Talk
          <kbd className="ml-auto rounded bg-black/15 px-1.5 py-0.5 text-[10px] font-medium">
            T
          </kbd>
        </button>
      </div>

      <div className="px-3 pb-3">
        <button
          onClick={() => togglePalette(true)}
          className="btn w-full justify-start gap-2.5 text-fg-subtle"
        >
          <Search className="h-4 w-4" />
          Search
          <kbd className="ml-auto rounded border bg-surface-2 px-1.5 py-0.5 text-[10px]">⌘K</kbd>
        </button>
      </div>

      <nav className="flex-1 space-y-0.5 overflow-y-auto px-3">
        <Link href="/" className={cn("nav-link", isActive("/") && "nav-link-active")}>
          <Home className="h-4 w-4" /> Home
        </Link>
        <Link href="/inbox" className={cn("nav-link", isActive("/inbox") && "nav-link-active")}>
          <Inbox className="h-4 w-4" /> Inbox
          {inboxCount > 0 && (
            <span className="ml-auto rounded-full bg-accent px-1.5 py-0.5 text-[10px] font-semibold text-accent-fg">
              {inboxCount}
            </span>
          )}
        </Link>
        <div className="pt-3">
          {NAV.map((n) => (
            <Link
              key={n.href}
              href={n.href}
              className={cn("nav-link", isActive(n.href) && "nav-link-active")}
            >
              <n.icon className="h-4 w-4" />
              {n.label}
            </Link>
          ))}
        </div>
      </nav>

      <div className="border-t p-3">
        <Link href="/settings" className={cn("nav-link", isActive("/settings") && "nav-link-active")}>
          <Settings className="h-4 w-4" /> Settings
        </Link>
      </div>
    </aside>
  );
}
