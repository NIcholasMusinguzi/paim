import { describe, expect, it } from "vitest";

import { humanStatus } from "./humanStatus";

describe("humanStatus", () => {
  it("never returns a raw status code or the word 'error' alone", () => {
    for (const code of [401, 403, 404, 409, 500, 502, 503]) {
      const message = humanStatus(code);
      expect(message).not.toMatch(/^\d+$/);
      expect(message.length).toBeGreaterThan(10);
    }
  });

  it("tells the user their work is safe on a 5xx", () => {
    expect(humanStatus(500)).toMatch(/stored on this phone/i);
  });

  it("gives a session-expired message on 401", () => {
    expect(humanStatus(401)).toMatch(/sign in again/i);
  });
});
