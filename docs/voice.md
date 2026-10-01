# Council — Voice

Two distinct voice paths. They are **not** the same system.

## 1. Recorded thought pipeline (asynchronous)

`Talk` → record audio in the browser (MediaRecorder + live waveform) → upload to
`POST /api/thoughts/audio` → store original (permanent) → STT (`faster-whisper` live /
deterministic mock) → raw transcript → refine → structure → routing → Thought Review → dispatch.

This is for *thinking out loud*; latency is not critical and the original is preserved forever.

## 2. Realtime voice (synchronous)

Distinct low-latency mode (spec §14), **not** the recorded pipeline faked. Architecture:

```
microphone → streaming STT / realtime model → persistent agent → streaming response → TTS
```

- `POST /api/voice/session` mints a room token via `RealtimeVoiceProvider`.
- Live provider: **LiveKit** (`LiveKitRealtimeProvider`) — turn detection, interruption/barge-in,
  partial transcript, mute, end, switch to text, transcript persistence, connection to agent memory.
  A LiveKit agent worker joins the room to run STT→LLM→TTS.
- Mock provider returns a demo token so the Talk-to-agent UI is exercisable offline.

### Pipecat
Evaluated as a reference. LiveKit covers our realtime needs with a smaller surface for the
single-user case. The `RealtimeVoiceProvider` interface means Pipecat can be swapped in later for
multi-agent fan-out without touching the rest of Council. We intentionally do **not** integrate both.

## 3. Council Call (multi-agent voice, spec §15)

`POST /api/voice/council-call` creates a multi-participant session with a **moderator** (Chief of
Staff). The moderator solicits relevant specialist views, identifies agreement/disagreement,
suppresses duplication and brings unresolved questions back to the user. For MVP the moderator may
call agents sequentially/parallel internally while presenting one coherent conversational response.
