"use client";

import { usePathname } from "next/navigation";
import { useEffect } from "react";

import { useUI } from "@/lib/store";
import { CommandPalette } from "./command-palette";
import { Sidebar } from "./sidebar";
import { TalkPanel } from "../talk/talk-panel";
import { Topbar } from "./topbar";

const TITLES: Record<string, string> = {
  "/": "Home",
  "/inbox": "Inbox",
  "/thoughts": "Thoughts",
  "/agents": "Agents",
  "/tasks": "Tasks",
  "/projects": "Projects",
  "/reports": "Reports",
  "/memory": "Memory Explorer",
  "/activity": "Activity",
  "/settings": "Settings",
};

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { openTalk, togglePalette, paletteOpen, talkOpen } = useUI();

  // Global keyboard shortcuts: ⌘K / Ctrl+K for palette, "T" for Talk.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement;
      const typing = ["INPUT", "TEXTAREA"].includes(target.tagName) || target.isContentEditable;
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        togglePalette();
      } else if (!typing && e.key.toLowerCase() === "t" && !paletteOpen && !talkOpen) {
        e.preventDefault();
        openTalk();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [openTalk, togglePalette, paletteOpen, talkOpen]);

  const title = TITLES[pathname] ?? (pathname.startsWith("/agents/") ? "Agent" : "Council");

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <Topbar title={title} />
        <main className="flex-1 overflow-y-auto">{children}</main>
      </div>
      <TalkPanel />
      <CommandPalette />
    </div>
  );
}
