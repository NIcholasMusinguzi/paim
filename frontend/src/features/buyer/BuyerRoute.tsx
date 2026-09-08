import { type FormEvent, useState } from "react";

import { ApiError } from "../../api/client";
import { Button } from "../../design/ui/Button";
import { EmptyState } from "../../design/ui/EmptyState";
import { Field } from "../../design/ui/Field";
import { Pill } from "../../design/ui/Pill";
import { useLogout } from "../../api/hooks/useMe";
import { useLotDetail, useOpenLots, useSubmitBid } from "./useLots";

function BidForm({ lotId }: { lotId: number }) {
  const submit = useSubmitBid(lotId);
  const [price, setPrice] = useState("");
  const [terms, setTerms] = useState("");

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    submit.mutate({ price_per_kg: Number(price), terms });
  }

  return (
    <form
      onSubmit={onSubmit}
      className="flex flex-col gap-3 rounded-lg bg-panel p-4"
    >
      <h3 className="text-sm font-semibold uppercase tracking-wide text-soft">
        Submit a sealed bid
      </h3>
      <Field
        label="Price (UGX/kg)"
        type="number"
        min={1}
        required
        value={price}
        onChange={(e) => setPrice(e.target.value)}
      />
      <Field
        label="Terms"
        required
        value={terms}
        onChange={(e) => setTerms(e.target.value)}
      />
      {submit.isError && (
        <p role="alert" className="text-sm text-murram">
          {submit.error instanceof ApiError
            ? submit.error.detail
            : "Something went wrong. Please try again."}
        </p>
      )}
      <Button type="submit" disabled={submit.isPending}>
        {submit.isPending ? "Submitting…" : "Submit bid"}
      </Button>
    </form>
  );
}

function LotDetailPanel({
  lotId,
  onClose,
}: {
  lotId: number;
  onClose: () => void;
}) {
  const { data: lot, isLoading } = useLotDetail(lotId);
  if (isLoading || !lot) return <div className="p-4 text-soft">Loading…</div>;

  const myBid = lot.bids[0];

  return (
    <div className="flex flex-col gap-4 rounded-lg bg-panel p-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-ink">
            {lot.crop} · {lot.parish}
          </h2>
          <p className="tabular text-sm text-soft">
            {lot.bags} / {lot.min_bags} bags ·{" "}
            <Pill tone="grain">{lot.status}</Pill>
          </p>
        </div>
        <Button variant="ghost" onClick={onClose}>
          Close
        </Button>
      </div>

      {lot.status === "open" ? (
        myBid ? (
          <p className="text-sm text-ink">
            Your bid:{" "}
            <span className="tabular">UGX {myBid.price_per_kg}/kg</span> —
            sealed until the lot closes. You cannot see other buyers' bids, and
            they cannot see yours.
          </p>
        ) : (
          <BidForm lotId={lotId} />
        )
      ) : (
        <div className="flex flex-col gap-2">
          <h3 className="text-sm font-semibold uppercase tracking-wide text-soft">
            Bids (disclosed at closure)
          </h3>
          {lot.bids.length === 0 ? (
            <EmptyState title="No bids were submitted for this lot." />
          ) : (
            <ul className="flex flex-col gap-1">
              {lot.bids.map((b) => (
                <li
                  key={b.id}
                  className="flex items-center justify-between text-sm"
                >
                  <span className="text-ink">{b.buyer_name}</span>
                  <span className="tabular text-ink">
                    UGX {b.price_per_kg}/kg
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}

function BuyerRoute() {
  const { data: lots, isLoading } = useOpenLots();
  const logout = useLogout();
  const [selected, setSelected] = useState<number | null>(null);

  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-4 p-4">
      <header className="flex items-center justify-between">
        <h1 className="text-lg font-semibold text-ink">Open lots</h1>
        <Button
          variant="ghost"
          onClick={() => logout.mutate()}
          disabled={logout.isPending}
        >
          Sign out
        </Button>
      </header>

      {selected != null && (
        <LotDetailPanel lotId={selected} onClose={() => setSelected(null)} />
      )}

      {isLoading ? (
        <div className="p-4 text-soft">Loading…</div>
      ) : !lots || lots.length === 0 ? (
        <EmptyState title="No lots are open for bidding right now." />
      ) : (
        <ul className="flex flex-col gap-2">
          {lots.map((lot) => (
            <li key={lot.id}>
              <button
                onClick={() => setSelected(lot.id)}
                className="flex w-full items-center justify-between rounded-lg bg-panel p-4 text-left hover:bg-page"
              >
                <span className="font-medium text-ink">
                  {lot.crop} · {lot.parish}
                </span>
                <span className="tabular text-sm text-soft">
                  {lot.bags} / {lot.min_bags} bags
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export const Component = BuyerRoute;
