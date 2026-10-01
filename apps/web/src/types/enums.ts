// Mirrors apps/api/app/core/enums.py — keep in sync.

export const ResponseMode = {
  TALK: "talk",
  QUICK: "quick",
  DEEP: "deep",
  REMEMBER: "remember",
  AUTO: "auto",
} as const;
export type ResponseMode = (typeof ResponseMode)[keyof typeof ResponseMode];

export const ThoughtStatus = {
  CAPTURED: "captured",
  TRANSCRIBING: "transcribing",
  REFINING: "refining",
  READY_FOR_REVIEW: "ready_for_review",
  DISPATCHED: "dispatched",
  FAILED: "failed",
} as const;
export type ThoughtStatus = (typeof ThoughtStatus)[keyof typeof ThoughtStatus];

export const AgentDispatchStatus = {
  QUEUED: "queued",
  PROCESSING: "processing",
  WAITING_FOR_USER: "waiting_for_user",
  COMPLETED: "completed",
  FAILED: "failed",
  CANCELLED: "cancelled",
} as const;
export type AgentDispatchStatus =
  (typeof AgentDispatchStatus)[keyof typeof AgentDispatchStatus];

export const MemoryScope = {
  GLOBAL: "global",
  AGENT: "agent",
  PROJECT: "project",
} as const;
export type MemoryScope = (typeof MemoryScope)[keyof typeof MemoryScope];

export const AUTONOMY_LABELS: Record<number, string> = {
  0: "Observe",
  1: "Recommend",
  2: "Create internal",
  3: "External w/ approval",
  4: "External whitelisted",
};

export const RESPONSE_MODE_LABELS: Record<ResponseMode, string> = {
  talk: "Talk",
  quick: "Quick feedback",
  deep: "Deep analysis",
  remember: "Just remember",
  auto: "Auto",
};
