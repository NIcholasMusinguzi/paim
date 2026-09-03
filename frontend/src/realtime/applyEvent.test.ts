import { QueryClient } from "@tanstack/react-query";
import { beforeEach, describe, expect, it } from "vitest";

import type { components } from "../api/schema";
import { qk } from "../app/queryClient";
import { applyEvent } from "./applyEvent";

type ParishDashboard = components["schemas"]["ParishDashboard"];

const PARISH_ID = 1;

function baseDashboard(): ParishDashboard {
  return {
    parish: { id: PARISH_ID, name: "Katosi", district: "Mukono" },
    lot: { id: 10, crop: "Maize", status: "open", bags: 4, min_bags: 10 },
    declarations: [
      { id: 100, farmer_name: "Grace Nabirye", bags: 4, grade: "ungraded", moisture_pct: null, created_at: "2026-01-01T00:00:00Z" },
    ],
    metrics: { pct_grade1: 0, bags_declared: 4, avg_price_per_kg: null, farmers_active: 1, computed_at: "2026-01-01T00:00:00Z" },
  };
}

describe("applyEvent", () => {
  let qc: QueryClient;

  beforeEach(() => {
    qc = new QueryClient();
    qc.setQueryData(qk.parishDashboard(PARISH_ID), baseDashboard());
  });

  it("patches the lot meter instantly on declaration.created, without fabricating the new row", () => {
    applyEvent(qc, PARISH_ID, {
      type: "declaration.created", at: "2026-01-01T00:00:01Z",
      lot_id: 10, declaration_id: 101, bags: 6, grade: "ungraded", lot_bags: 10, lot_min_bags: 10,
    });
    const data = qc.getQueryData<ParishDashboard>(qk.parishDashboard(PARISH_ID));
    expect(data?.lot).toEqual({ id: 10, crop: "Maize", status: "open", bags: 10, min_bags: 10 });
    // The event carries no farmer name for the new row, so the declaration
    // list itself is not fabricated here — it comes from the refetch this
    // triggers (verified by the query being marked stale/invalidated).
    expect(qc.getQueryState(qk.parishDashboard(PARISH_ID))?.isInvalidated).toBe(true);
  });

  it("patches an existing declaration's grade and pct_grade1 on declaration.graded", () => {
    applyEvent(qc, PARISH_ID, {
      type: "declaration.graded", at: "2026-01-01T00:00:01Z",
      declaration_id: 100, grade: "grade_1", moisture_pct: "12.5", pct_grade1: 100,
    });
    const data = qc.getQueryData<ParishDashboard>(qk.parishDashboard(PARISH_ID));
    expect(data?.declarations[0]).toMatchObject({ grade: "grade_1", moisture_pct: "12.5" });
    expect(data?.metrics?.pct_grade1).toBe(100);
  });

  it("does not patch a declaration that is not in the current page", () => {
    applyEvent(qc, PARISH_ID, {
      type: "declaration.graded", at: "2026-01-01T00:00:01Z",
      declaration_id: 999, grade: "grade_1", moisture_pct: "12.5", pct_grade1: 100,
    });
    const data = qc.getQueryData<ParishDashboard>(qk.parishDashboard(PARISH_ID));
    expect(data?.declarations).toHaveLength(1);
    expect(data?.declarations[0].grade).toBe("ungraded");
  });

  it("invalidates rather than reconstructing state on lot.closed", () => {
    applyEvent(qc, PARISH_ID, { type: "lot.closed", at: "2026-01-01T00:00:01Z", lot_id: 10, bags: 10, bid_count: 2 });
    const data = qc.getQueryData<ParishDashboard>(qk.parishDashboard(PARISH_ID));
    // The cached snapshot is untouched — closing a lot changes which bids
    // are visible and what actions are available, which this client must
    // not reconstruct from a partial payload.
    expect(data?.lot?.status).toBe("open");
    expect(qc.getQueryState(qk.parishDashboard(PARISH_ID))?.isInvalidated).toBe(true);
  });

  it("ignores the hello event", () => {
    applyEvent(qc, PARISH_ID, { type: "hello", server_time: "2026-01-01T00:00:00Z" });
    expect(qc.getQueryState(qk.parishDashboard(PARISH_ID))?.isInvalidated).toBe(false);
  });

  it("two declaration.created events for the same lot patch idempotently, not doubling bags", () => {
    const event = {
      type: "declaration.created" as const, at: "2026-01-01T00:00:01Z",
      lot_id: 10, declaration_id: 101, bags: 6, grade: "ungraded", lot_bags: 10, lot_min_bags: 10,
    };
    applyEvent(qc, PARISH_ID, event);
    applyEvent(qc, PARISH_ID, event); // e.g. a duplicate delivery
    const data = qc.getQueryData<ParishDashboard>(qk.parishDashboard(PARISH_ID));
    expect(data?.lot?.bags).toBe(10); // set from the payload, not accumulated
  });
});
