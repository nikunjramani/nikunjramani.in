import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { timeAgo } from "./format";

describe("timeAgo", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-10-13T12:00:00Z"));
  });
  afterEach(() => vi.useRealTimers());

  it("formats ISO strings and epoch milliseconds alike", () => {
    expect(timeAgo("2026-10-13T11:59:50Z")).toBe("just now");
    expect(timeAgo("2026-10-13T11:55:00Z")).toBe("5m ago");
    expect(timeAgo(Date.parse("2026-10-13T09:00:00Z"))).toBe("3h ago");
    expect(timeAgo("2026-10-11T12:00:00Z")).toBe("2d ago");
  });

  it("renders nothing for a missing timestamp", () => {
    expect(timeAgo(undefined)).toBe("");
    expect(timeAgo(null)).toBe("");
  });
});
