import type { components } from "../../api/schema";
import { queryClient } from "../../app/queryClient";
import { bootstrap } from "./bootstrap";
import { db, type QueuedOp } from "./db";
import { deviceId } from "./deviceId";

type SyncResult = components["schemas"]["SyncResult"];

const MAX_ATTEMPTS = 6;
const BASE = import.meta.env.VITE_API_BASE ?? "/api/v1";

function csrf(): string {
  return document.cookie.match(/csrftoken=([^;]+)/)?.[1] ?? "";
}

let syncing: Promise<void> | null = null;

// Background sync on connectivity plus a manual "Sync now" control
// (IMPLEMENTATION.md section 9). Never runs two batches concurrently.
export function syncNow(): Promise<void> {
  syncing ??= runSync().finally(() => {
    syncing = null;
  });
  return syncing;
}

async function runSync(): Promise<void> {
  const ops = await db.outbox.where("status").equals("queued").toArray();
  if (ops.length > 0) {
    const ok = await postBatch(ops);
    if (!ok) {
      await bumpAttempts(ops);
      return;
    }
  }
  try {
    await bootstrap();
  } catch {
    // Bootstrap refresh is best-effort; the outbox flush above already ran.
  }
}

async function postBatch(ops: QueuedOp[]): Promise<boolean> {
  let res: Response;
  try {
    res = await fetch(`${BASE}/sync/batch/`, {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json", "X-CSRFToken": csrf() },
      body: JSON.stringify({
        device_id: deviceId(),
        operations: ops.map(({ op_id, type, payload, at }) => ({ op_id, type, payload, at })),
      }),
    });
  } catch {
    return false;
  }
  if (!res.ok) return false;

  const body: { results: SyncResult[] } = await res.json();
  for (const r of body.results) {
    if (r.status === "applied") {
      await db.outbox.update(r.op_id, { status: "applied" });
      if (r.farmer_id !== undefined) await reconcileFarmer(r.op_id, r.farmer_id);
    } else {
      await db.outbox.update(r.op_id, { status: "rejected", reason: r.reason });
      await flagNeedsAttention(r.op_id, r.reason);
    }
  }
  queryClient.invalidateQueries({ queryKey: ["agent"] });
  return true;
}

async function bumpAttempts(ops: QueuedOp[]): Promise<void> {
  for (const op of ops) {
    const attempts = op.attempts + 1;
    const capped = attempts >= MAX_ATTEMPTS;
    await db.outbox.update(op.op_id, {
      attempts,
      status: capped ? "needs_attention" : "queued",
      reason: capped ? "sync_failed" : undefined,
    });
    if (capped) await flagNeedsAttention(op.op_id, "sync_failed");
  }
}

async function reconcileFarmer(opId: string, farmerId: number): Promise<void> {
  const local = await db.farmers.where("op_id").equals(opId).first();
  if (!local || local.id === farmerId) return;
  await db.farmers.delete(local.id);
  await db.farmers.put({ ...local, id: farmerId, pending: false });
}

async function flagNeedsAttention(opId: string, reason?: string): Promise<void> {
  const local = await db.farmers.where("op_id").equals(opId).first();
  if (!local) return;
  await db.farmers.update(local.id, { needs_attention: true, reason });
}
