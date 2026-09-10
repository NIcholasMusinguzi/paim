import { type FormEvent, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { ApiError, api } from "../../api/client";
import { useAuth } from "../../app/AuthProvider";
import { formatUgx } from "../../design/format";
import { Button } from "../../design/ui/Button";
import { Card } from "../../design/ui/Card";
import { EmptyState } from "../../design/ui/EmptyState";
import { Field } from "../../design/ui/Field";
import { Pill } from "../../design/ui/Pill";

export type LotBid = {
  id: number;
  buyer_name: string;
  price_per_kg: number;
  terms: string;
  submitted_at: string;
};

export type LotRow = {
  id: number;
  parish: string;
  crop: string;
  status: string;
  bags: number;
  min_bags: number;
  bid_count: number;
  bids: LotBid[];
  awarded_buyer: string | null;
  awarded_price_per_kg: number | null;
};

const CAN_AWARD = new Set(["parish_chief", "subcounty_officer"]);

function useLots() {
  return useQuery({
    queryKey: ["lots"] as const,
    queryFn: () => api<LotRow[]>("/lots/"),
  });
}

function AwardForm({ lot }: { lot: LotRow }) {
  const qc = useQueryClient();
  const award = useMutation({
    mutationFn: (body: { bid_id: number; committee_minute_ref: string }) =>
      api<LotRow>(`/lots/${lot.id}/award/`, { method: "POST", body: JSON.stringify(body) }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["lots"] }),
  });
  const [bidId, setBidId] = useState(String(lot.bids[0]?.id ?? ""));
  const [minute, setMinute] = useState("");

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    award.mutate({ bid_id: Number(bidId), committee_minute_ref: minute });
  }

  if (lot.bids.length === 0) {
    return <p className="text-sm text-soft">No disclosed bids to award yet.</p>;
  }

  return (
    <form onSubmit={onSubmit} className="mt-3 flex flex-col gap-2 border-t border-rule pt-3">
      <label className="text-xs font-medium text-soft">
        Winning bid
        <select
          className="mt-1 w-full rounded-lg border border-rule bg-panel px-3 py-2 text-sm text-ink"
          value={bidId}
          onChange={(e) => setBidId(e.target.value)}
        >
          {lot.bids.map((b) => (
            <option key={b.id} value={b.id}>
              {b.buyer_name} · {formatUgx(b.price_per_kg)}/kg
            </option>
          ))}
        </select>
      </label>
      <Field
        label="Committee minute ref"
        required
        value={minute}
        onChange={(e) => setMinute(e.target.value)}
      />
      {award.isError && (
        <p role="alert" className="text-sm text-murram">
          {award.error instanceof ApiError ? award.error.detail : "Could not award this lot."}
        </p>
      )}
      <Button type="submit" disabled={award.isPending} className="self-start">
        {award.isPending ? "Awarding…" : "Award lot"}
      </Button>
    </form>
  );
}

function BidsRoute() {
  const { me } = useAuth();
  const { data: lots, isLoading, isError, error } = useLots();
  const [openId, setOpenId] = useState<number | null>(null);
  const canAward = me != null && CAN_AWARD.has(me.role);

  return (
    <Card title="Lots and bids">
      {isLoading ? (
        <p className="text-soft">Loading…</p>
      ) : isError ? (
        <EmptyState
          title={error instanceof ApiError ? error.detail : "Could not load lots."}
        />
      ) : !lots || lots.length === 0 ? (
        <EmptyState title="No lots in your scope yet." />
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-rule text-xs text-soft">
                <th className="py-2">Parish</th>
                <th>Crop</th>
                <th>Status</th>
                <th>Bags</th>
                <th>Bids</th>
                <th>Awarded</th>
              </tr>
            </thead>
            <tbody>
              {lots.map((lot) => (
                <tr key={lot.id} className="border-b border-rule last:border-0">
                  <td className="py-2.5 text-ink">{lot.parish}</td>
                  <td className="text-ink">{lot.crop}</td>
                  <td>
                    <Pill tone={lot.status === "awarded" || lot.status === "settled" ? "leaf" : "grain"}>
                      {lot.status}
                    </Pill>
                  </td>
                  <td className="tabular">
                    {lot.bags} / {lot.min_bags}
                  </td>
                  <td>
                    <button
                      type="button"
                      className="text-sm font-medium text-leaf"
                      onClick={() => setOpenId(openId === lot.id ? null : lot.id)}
                    >
                      {lot.bid_count} bid{lot.bid_count === 1 ? "" : "s"}
                    </button>
                  </td>
                  <td className="text-ink">
                    {lot.awarded_buyer
                      ? `${lot.awarded_buyer} · ${formatUgx(lot.awarded_price_per_kg)}/kg`
                      : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {lots.map((lot) =>
            openId === lot.id ? (
              <div key={`detail-${lot.id}`} className="mt-3 rounded-lg bg-page p-3">
                <p className="text-sm font-medium text-ink">
                  {lot.crop} · {lot.parish}
                </p>
                {lot.status === "open" && lot.bids.length === 0 ? (
                  <p className="mt-1 text-sm text-soft">
                    {lot.bid_count} sealed bid{lot.bid_count === 1 ? "" : "s"}. Prices are hidden until the lot closes.
                  </p>
                ) : lot.bids.length === 0 ? (
                  <EmptyState title="No bids on this lot." />
                ) : (
                  <ul className="mt-2 flex flex-col gap-1 text-sm">
                    {lot.bids.map((b) => (
                      <li key={b.id} className="flex justify-between gap-3">
                        <span className="text-ink">{b.buyer_name}</span>
                        <span className="tabular text-ink">
                          {formatUgx(b.price_per_kg)}/kg · {b.terms}
                        </span>
                      </li>
                    ))}
                  </ul>
                )}
                {canAward && lot.status === "closed" && <AwardForm lot={lot} />}
              </div>
            ) : null,
          )}
        </div>
      )}
    </Card>
  );
}

export const Component = BidsRoute;
