"use client";

import { Check, Play, Send } from "lucide-react";
import { useState } from "react";

import { api } from "@/lib/api";
import { useAgents, useDispatchThought } from "@/lib/hooks";
import { ResponseMode, RESPONSE_MODE_LABELS } from "@/types";
import type { Thought } from "@/types";
import { cn, confidenceColor } from "@/lib/utils";

const MODES: ResponseMode[] = ["quick", "deep", "remember", "talk", "auto"];

export function ThoughtReview({ thought, onDone }: { thought: Thought; onDone: () => void }) {
  const { data: agentsData } = useAgents();
  const dispatch = useDispatchThought();

  // Pre-select recipients from routing suggestions >= 0.5 confidence.
  const [selected, setSelected] = useState<Set<string>>(
    () => new Set(thought.routing_suggestions.filter((s) => s.confidence >= 0.5).map((s) => s.agent_id)),
  );
  const [mode, setMode] = useState<ResponseMode>("auto");
  const [cleanText, setCleanText] = useState(thought.clean_transcript);
  const [showRaw, setShowRaw] = useState(false);

  const suggestionMap = new Map(thought.routing_suggestions.map((s) => [s.agent_id, s]));
  const agents = (agentsData?.items ?? []).filter((a) => !a.is_supervisor);
  const audioUrl = api.storageUrl(thought.original_audio_uri);

  const toggle = (id: string) =>
    setSelected((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });

  const submit = async () => {
    await dispatch.mutateAsync({
      id: thought.id,
      body: { recipient_agent_ids: [...selected], response_mode: mode },
    });
    onDone();
  };

  return (
    <div className="max-h-[72vh] overflow-y-auto p-5">
      <div className="mb-4">
        <div className="section-label mb-1">Title</div>
        <div className="text-lg font-semibold leading-tight">{thought.title}</div>
      </div>

      <div className="mb-4">
        <div className="mb-1 flex items-center justify-between">
          <span className="section-label">Clean thought</span>
          <div className="flex gap-2">
            {audioUrl && (
              <a href={audioUrl} target="_blank" rel="noreferrer" className="chip hover:bg-surface">
                <Play className="h-3 w-3" /> Listen
              </a>
            )}
            <button onClick={() => setShowRaw((v) => !v)} className="chip hover:bg-surface">
              {showRaw ? "Hide raw" : "Raw transcript"}
            </button>
          </div>
        </div>
        <textarea
          value={cleanText}
          onChange={(e) => setCleanText(e.target.value)}
          rows={4}
          className="input resize-none text-sm leading-relaxed"
        />
        {showRaw && (
          <p className="mt-2 rounded-md border bg-surface-2 p-2 text-xs italic text-fg-subtle">
            {thought.raw_transcript}
          </p>
        )}
      </div>

      {thought.topics.length > 0 && (
        <Section label="Topics">
          <div className="flex flex-wrap gap-1.5">
            {thought.topics.map((t) => (
              <span key={t} className="chip">{t}</span>
            ))}
          </div>
        </Section>
      )}

      {thought.questions.length > 0 && (
        <Section label="Questions">
          <ul className="space-y-1 text-sm text-fg-subtle">
            {thought.questions.map((q, i) => (
              <li key={i}>• {q}</li>
            ))}
          </ul>
        </Section>
      )}

      <Section label="Send to">
        <div className="grid grid-cols-2 gap-1.5">
          {agents.map((a) => {
            const sug = suggestionMap.get(a.id);
            const on = selected.has(a.id);
            return (
              <button
                key={a.id}
                onClick={() => toggle(a.id)}
                className={cn(
                  "flex items-center gap-2 rounded-md border px-2.5 py-2 text-left text-sm transition-colors",
                  on ? "border-accent/50 bg-accent/10" : "hover:bg-surface-2",
                )}
              >
                <span
                  className={cn(
                    "grid h-4 w-4 shrink-0 place-items-center rounded border",
                    on && "border-accent bg-accent text-accent-fg",
                  )}
                >
                  {on && <Check className="h-3 w-3" />}
                </span>
                <span className="min-w-0 flex-1 truncate">{a.name}</span>
                {sug && (
                  <span className={cn("font-mono text-[11px]", confidenceColor(sug.confidence))}>
                    {sug.confidence.toFixed(2)}
                  </span>
                )}
              </button>
            );
          })}
        </div>
      </Section>

      <Section label="Response mode">
        <div className="flex flex-wrap gap-1.5">
          {MODES.map((m) => (
            <button
              key={m}
              onClick={() => setMode(m)}
              className={cn("chip cursor-pointer", mode === m && "border-accent bg-accent/10 text-fg")}
            >
              {RESPONSE_MODE_LABELS[m]}
            </button>
          ))}
        </div>
      </Section>

      <button
        onClick={submit}
        disabled={selected.size === 0 || dispatch.isPending}
        className="btn btn-primary mt-5 w-full"
      >
        <Send className="h-4 w-4" />
        {dispatch.isPending ? "Dispatching…" : `Dispatch to ${selected.size} agent${selected.size === 1 ? "" : "s"}`}
      </button>
    </div>
  );
}

function Section({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="mb-4">
      <div className="section-label mb-1.5">{label}</div>
      {children}
    </div>
  );
}
