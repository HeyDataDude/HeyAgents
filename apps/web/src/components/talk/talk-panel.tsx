"use client";

import { Keyboard, Mic, Type, X } from "lucide-react";
import { useState } from "react";

import { useCreateTextThought, useUploadAudioThought } from "@/lib/hooks";
import { useUI } from "@/lib/store";
import { Recorder } from "./recorder";
import { ThoughtReview } from "./thought-review";
import type { Thought } from "@/types";

type Stage = "capture" | "processing" | "review";

export function TalkPanel() {
  const { talkOpen, closeTalk } = useUI();
  const [mode, setMode] = useState<"voice" | "text">("voice");
  const [stage, setStage] = useState<Stage>("capture");
  const [text, setText] = useState("");
  const [thought, setThought] = useState<Thought | null>(null);

  const uploadAudio = useUploadAudioThought();
  const createText = useCreateTextThought();

  if (!talkOpen) return null;

  const reset = () => {
    setStage("capture");
    setText("");
    setThought(null);
    setMode("voice");
  };
  const close = () => {
    reset();
    closeTalk();
  };

  const handleAudio = async (blob: Blob) => {
    setStage("processing");
    const form = new FormData();
    form.append("file", blob, "recording.webm");
    form.append("source", "talk");
    const t = await uploadAudio.mutateAsync(form);
    setThought(t);
    setStage("review");
  };

  const handleText = async () => {
    if (!text.trim()) return;
    setStage("processing");
    const t = await createText.mutateAsync({ text });
    setThought(t);
    setStage("review");
  };

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center bg-black/40 p-4 backdrop-blur-sm sm:items-center">
      <div className="card w-full max-w-xl overflow-hidden shadow-panel">
        <div className="flex items-center justify-between border-b px-5 py-3">
          <div className="flex items-center gap-2">
            <span className="grid h-6 w-6 place-items-center rounded-md bg-accent text-accent-fg">
              <Mic className="h-3.5 w-3.5" />
            </span>
            <span className="text-sm font-semibold">
              {stage === "review" ? "New thought" : "Talk"}
            </span>
          </div>
          <button onClick={close} className="btn h-7 w-7 p-0" aria-label="Close">
            <X className="h-4 w-4" />
          </button>
        </div>

        {stage === "capture" && (
          <div className="p-6">
            <div className="mb-5 flex justify-center gap-1 rounded-md border bg-surface-2 p-1 text-sm">
              <button
                onClick={() => setMode("voice")}
                className={`flex-1 rounded px-3 py-1.5 ${mode === "voice" ? "bg-surface shadow-soft" : "text-fg-subtle"}`}
              >
                <Mic className="mr-1.5 inline h-3.5 w-3.5" /> Voice
              </button>
              <button
                onClick={() => setMode("text")}
                className={`flex-1 rounded px-3 py-1.5 ${mode === "text" ? "bg-surface shadow-soft" : "text-fg-subtle"}`}
              >
                <Type className="mr-1.5 inline h-3.5 w-3.5" /> Text
              </button>
            </div>

            {mode === "voice" ? (
              <Recorder onComplete={handleAudio} />
            ) : (
              <div>
                <p className="mb-2 text-center text-sm text-fg-subtle">
                  Think out loud — just write however it comes.
                </p>
                <textarea
                  autoFocus
                  value={text}
                  onChange={(e) => setText(e.target.value)}
                  rows={5}
                  placeholder="I was thinking about…"
                  className="input resize-none"
                />
                <button
                  onClick={handleText}
                  disabled={!text.trim()}
                  className="btn btn-primary mt-3 w-full"
                >
                  Capture thought
                </button>
              </div>
            )}
            <p className="mt-4 flex items-center justify-center gap-1.5 text-[11px] text-muted">
              <Keyboard className="h-3 w-3" /> Press T anywhere to start talking
            </p>
          </div>
        )}

        {stage === "processing" && (
          <div className="flex flex-col items-center gap-3 p-12">
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-border border-t-accent" />
            <p className="text-sm text-fg-subtle">Transcribing & understanding…</p>
          </div>
        )}

        {stage === "review" && thought && (
          <ThoughtReview thought={thought} onDone={close} />
        )}
      </div>
    </div>
  );
}
