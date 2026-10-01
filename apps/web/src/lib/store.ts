"use client";

import { create } from "zustand";

interface UIState {
  talkOpen: boolean;
  paletteOpen: boolean;
  reviewThoughtId: string | null;
  openTalk: () => void;
  closeTalk: () => void;
  togglePalette: (open?: boolean) => void;
  setReviewThought: (id: string | null) => void;
}

export const useUI = create<UIState>((set) => ({
  talkOpen: false,
  paletteOpen: false,
  reviewThoughtId: null,
  openTalk: () => set({ talkOpen: true }),
  closeTalk: () => set({ talkOpen: false }),
  togglePalette: (open) => set((s) => ({ paletteOpen: open ?? !s.paletteOpen })),
  setReviewThought: (id) => set({ reviewThoughtId: id }),
}));
