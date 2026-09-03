import type { QueryClient } from "@tanstack/react-query";

import type { components } from "../api/schema";
import { qk } from "../app/queryClient";
import type { ServerEvent } from "./events";

type ParishDashboard = components["schemas"]["ParishDashboard"];

// Incremental events patch the cache; structural events invalidate. A lot
// closing changes which bids are visible and what actions are available —
// reconstructing that client-side would duplicate backend rules in
// TypeScript (IMPLEMENTATION_REACT.md section 6.2).
export function applyEvent(qc: QueryClient, parishId: number, event: ServerEvent): void {
  switch (event.type) {
    case "hello":
      return;

    case "declaration.created":
      // Patch the meter instantly; the payload has no farmer name for the
      // new row, so the declaration list itself comes from a refetch.
      qc.setQueryData(qk.parishDashboard(parishId), (old?: ParishDashboard) =>
        old && {
          ...old,
          lot: old.lot && { ...old.lot, bags: event.lot_bags, min_bags: event.lot_min_bags },
        });
      qc.invalidateQueries({ queryKey: qk.parishDashboard(parishId) });
      return;

    case "declaration.graded":
      qc.setQueryData(qk.parishDashboard(parishId), (old?: ParishDashboard) =>
        old && {
          ...old,
          metrics: old.metrics && { ...old.metrics, pct_grade1: event.pct_grade1 },
          declarations: old.declarations.map((d) =>
            d.id === event.declaration_id ? { ...d, grade: event.grade, moisture_pct: event.moisture_pct } : d,
          ),
        });
      return;

    case "lot.closed":
      // Structural change — do not reconstruct it from the payload, refetch.
      qc.invalidateQueries({ queryKey: qk.parishDashboard(parishId) });
      return;
  }
}
