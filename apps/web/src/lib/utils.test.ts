import { describe, expect, it } from "vitest";

import { confidenceColor, formatDuration, timeAgo } from "./utils";

describe("formatDuration", () => {
  it("formats seconds as m:ss", () => {
    expect(formatDuration(0)).toBe("0:00");
    expect(formatDuration(5)).toBe("0:05");
    expect(formatDuration(65)).toBe("1:05");
    expect(formatDuration(600)).toBe("10:00");
  });
  it("handles nullish", () => {
    expect(formatDuration(null)).toBe("0:00");
    expect(formatDuration(undefined)).toBe("0:00");
  });
});

describe("confidenceColor", () => {
  it("maps confidence to tiers", () => {
    expect(confidenceColor(0.95)).toContain("emerald");
    expect(confidenceColor(0.6)).toContain("amber");
    expect(confidenceColor(0.1)).toContain("muted");
  });
});

describe("timeAgo", () => {
  it("returns 'just now' for recent", () => {
    expect(timeAgo(new Date().toISOString())).toBe("just now");
  });
  it("returns minutes for a few minutes ago", () => {
    const d = new Date(Date.now() - 5 * 60 * 1000).toISOString();
    expect(timeAgo(d)).toBe("5m ago");
  });
});
