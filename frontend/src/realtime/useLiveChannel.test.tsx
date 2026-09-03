import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { qk } from "../app/queryClient";
import { useLiveChannel } from "./useLiveChannel";

class FakeWebSocket {
  static instances: FakeWebSocket[] = [];
  onopen: (() => void) | null = null;
  onclose: ((e: { code: number }) => void) | null = null;
  onmessage: ((e: { data: string }) => void) | null = null;
  closed = false;

  constructor(public url: string) {
    FakeWebSocket.instances.push(this);
  }

  close() {
    this.closed = true;
  }

  triggerOpen() {
    this.onopen?.();
  }

  triggerClose(code: number) {
    this.onclose?.({ code });
  }
}

function wrapper(qc: QueryClient) {
  return ({ children }: { children: ReactNode }) => <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
}

describe("useLiveChannel", () => {
  let qc: QueryClient;

  beforeEach(() => {
    FakeWebSocket.instances = [];
    vi.stubGlobal("WebSocket", FakeWebSocket);
    qc = new QueryClient();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.useRealTimers();
  });

  it("does not retry after a 4403 close (not permitted, do not retry)", async () => {
    const { result } = renderHook(() => useLiveChannel(1), { wrapper: wrapper(qc) });
    await waitFor(() => expect(FakeWebSocket.instances).toHaveLength(1));

    FakeWebSocket.instances[0].triggerClose(4403);
    await waitFor(() => expect(result.current.status).toBe("offline"));

    // Give any (incorrect) retry timer a chance to fire.
    await new Promise((r) => setTimeout(r, 50));
    expect(FakeWebSocket.instances).toHaveLength(1);
  });

  it("clears the session on a 4401 close instead of retrying", async () => {
    qc.setQueryData(qk.me, { id: 1 });
    renderHook(() => useLiveChannel(1), { wrapper: wrapper(qc) });
    await waitFor(() => expect(FakeWebSocket.instances).toHaveLength(1));

    FakeWebSocket.instances[0].triggerClose(4401);
    await waitFor(() => expect(qc.getQueryData(qk.me)).toBeNull());
    expect(FakeWebSocket.instances).toHaveLength(1);
  });

  it("refetches the parish dashboard on reconnect, since WebSocket events are not a durable log", async () => {
    qc.setQueryData(qk.parishDashboard(1), { stale: true });
    const invalidateSpy = vi.spyOn(qc, "invalidateQueries");

    const { result } = renderHook(() => useLiveChannel(1), { wrapper: wrapper(qc) });
    await waitFor(() => expect(FakeWebSocket.instances).toHaveLength(1));
    FakeWebSocket.instances[0].triggerOpen();
    await waitFor(() => expect(result.current.status).toBe("open"));
    invalidateSpy.mockClear();

    // Connection drops for a reason that should retry (not 4401/4403).
    FakeWebSocket.instances[0].triggerClose(1006);
    await waitFor(() => expect(result.current.status).toBe("reconnecting"));

    await waitFor(() => expect(FakeWebSocket.instances).toHaveLength(2), { timeout: 3000 });
    FakeWebSocket.instances[1].triggerOpen();

    await waitFor(() => expect(result.current.status).toBe("open"));
    expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: qk.parishDashboard(1) });
  });
});
