"use client";

import { Mic, Square } from "lucide-react";
import { useEffect, useRef, useState } from "react";

import { formatDuration } from "@/lib/utils";

/**
 * Voice recorder with live waveform, duration and cancel.
 * Uses the MediaRecorder + Web Audio APIs. Falls back gracefully if the mic is
 * unavailable (e.g. permissions denied) by letting the user switch to text.
 */
export function Recorder({ onComplete }: { onComplete: (blob: Blob) => void }) {
  const [recording, setRecording] = useState(false);
  const [seconds, setSeconds] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [levels, setLevels] = useState<number[]>(Array(32).fill(0.1));

  const mediaRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);
  const rafRef = useRef<number>();
  const analyserRef = useRef<AnalyserNode | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval>>();

  const stopEverything = () => {
    if (rafRef.current) cancelAnimationFrame(rafRef.current);
    if (timerRef.current) clearInterval(timerRef.current);
    streamRef.current?.getTracks().forEach((t) => t.stop());
  };

  useEffect(() => () => stopEverything(), []);

  const start = async () => {
    setError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      const AudioCtx = window.AudioContext || (window as any).webkitAudioContext;
      const ctx = new AudioCtx();
      const source = ctx.createMediaStreamSource(stream);
      const analyser = ctx.createAnalyser();
      analyser.fftSize = 64;
      source.connect(analyser);
      analyserRef.current = analyser;

      const data = new Uint8Array(analyser.frequencyBinCount);
      const tick = () => {
        analyser.getByteFrequencyData(data);
        setLevels(Array.from(data.slice(0, 32)).map((v) => Math.max(0.08, v / 255)));
        rafRef.current = requestAnimationFrame(tick);
      };
      tick();

      const rec = new MediaRecorder(stream);
      chunksRef.current = [];
      rec.ondataavailable = (e) => e.data.size > 0 && chunksRef.current.push(e.data);
      rec.start();
      mediaRef.current = rec;

      setRecording(true);
      setSeconds(0);
      timerRef.current = setInterval(() => setSeconds((s) => s + 1), 1000);
    } catch {
      setError("Microphone unavailable. Switch to Text mode above, or allow mic access.");
    }
  };

  const stop = () => {
    const rec = mediaRef.current;
    if (!rec) return;
    rec.onstop = () => {
      const blob = new Blob(chunksRef.current, { type: "audio/webm" });
      onComplete(blob);
    };
    rec.stop();
    setRecording(false);
    stopEverything();
  };

  return (
    <div className="flex flex-col items-center gap-6 py-4">
      <div className="flex h-16 items-end gap-[3px]">
        {levels.map((lvl, i) => (
          <div
            key={i}
            className="w-1.5 rounded-full bg-accent/70 transition-[height] duration-75"
            style={{ height: `${Math.round(lvl * 64)}px` }}
          />
        ))}
      </div>

      <div className="font-mono text-2xl tabular-nums text-fg-subtle">
        {formatDuration(seconds)}
      </div>

      {!recording ? (
        <button
          onClick={start}
          className="grid h-16 w-16 place-items-center rounded-full bg-accent text-accent-fg shadow-panel transition-transform hover:scale-105"
          aria-label="Start recording"
        >
          <Mic className="h-7 w-7" />
        </button>
      ) : (
        <button
          onClick={stop}
          className="recording-pulse grid h-16 w-16 place-items-center rounded-full bg-red-500 text-white transition-transform hover:scale-105"
          aria-label="Stop recording"
        >
          <Square className="h-6 w-6 fill-current" />
        </button>
      )}

      <p className="text-xs text-muted">
        {recording ? "Recording — tap to stop" : "Tap to start recording"}
      </p>
      {error && <p className="max-w-xs text-center text-xs text-red-500">{error}</p>}
    </div>
  );
}
