import { describe, expect, it } from "vitest";

import { formatInt, formatUgx, initials } from "./format";

describe("format helpers", () => {
  it("formats integers with grouping", () => {
    expect(formatInt(1248)).toBe("1,248");
    expect(formatInt(null)).toBe("—");
  });

  it("formats UGX prices", () => {
    expect(formatUgx(1200)).toBe("UGX 1,200");
    expect(formatUgx(null)).toBe("—");
  });

  it("builds initials from a full name", () => {
    expect(initials("John Bosco")).toBe("JB");
    expect(initials("Amina")).toBe("AM");
  });
});
