import { useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef, useState } from "react";

import { qk } from "../app/queryClient";
import { applyEvent } from "./applyEvent";
import type { ServerEvent } from "./events";

export type LiveStatus = "connecting" | "open" | "reconnecting" | "offline";

export interface LiveChannelState {
  status: LiveStatus;
  lastEventAt: Date | null;
}

// One socket per parish dashboard, shared through the component that opens
// it. Reconnect uses capped exponential backoff with jitter, and — because
// WebSocket events are not a durable log — a reconnect always refetches
// rather than assuming nothing was missed while disconnected
// (IMPLEMENTATION_REACT.md section 6.1).
export function useLiveChannel(parishId: number | null): LiveChannelState {
  const [status, setStatus] = useState<LiveStatus>("connecting");
  const [lastEventAt, setLastEventAt] = useState<Date | null>(null);
  const qc = useQueryClient();
  const attempt = useRef(0);

  useEffect(() => {
    if (parishId == null) return;
    let closed = false;
    let timer: ReturnType<typeof setTimeout>;
    let sock: WebSocket | null = null;

    const open = () => {
      const proto = location.protocol === "https:" ? "wss" : "ws";
      sock = new WebSocket(`${proto}://${location.host}/ws/parish/${parishId}/`);
      setStatus(attempt.current === 0 ? "connecting" : "reconnecting");

      sock.onopen = () => {
        const reconnected = attempt.current > 0;
        attempt.current = 0;
        setStatus("open");
        if (reconnected) qc.invalidateQueries({ queryKey: qk.parishDashboard(parishId) });
      };

      sock.onmessage = (e) => {
        const event = JSON.parse(e.data) as ServerEvent;
        if (event.type !== "hello") setLastEventAt(new Date());
        applyEvent(qc, parishId, event);
      };

      sock.onclose = (e) => {
        if (closed) return;
        if (e.code === 4401) {
          qc.setQueryData(qk.me, null);
          return;
        }
        if (e.code === 4403) {
          setStatus("offline"); // not permitted, do not retry
          return;
        }
        const delay = Math.min(30_000, 1_000 * 2 ** attempt.current++) + Math.random() * 500;
        setStatus("reconnecting");
        timer = setTimeout(open, delay);
      };
    };

    open();
    return () => {
      closed = true;
      clearTimeout(timer);
      sock?.close();
    };
  }, [parishId, qc]);

  return { status, lastEventAt };
}
