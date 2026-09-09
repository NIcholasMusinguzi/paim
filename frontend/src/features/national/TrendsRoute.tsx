import { Card } from "../../design/ui/Card";
import { ApiError } from "../../api/client";
import { Button } from "../../design/ui/Button";
import { EmptyState } from "../../design/ui/EmptyState";
import { Pill } from "../../design/ui/Pill";
import { type TrendInsight, useApproveTrend, useTrends } from "./useTrends";

function PendingRow({ insight }: { insight: TrendInsight }) {
  const approve = useApproveTrend();
  return (
    <li className="flex flex-col gap-2 rounded-xl border border-rule bg-page p-4">
      <div className="flex items-center gap-2 text-xs text-soft">
        <Pill tone="grain">{insight.crop}</Pill>
        <span>{insight.scope_level}</span>
      </div>
      <p className="text-sm text-ink">{insight.message}</p>
      {approve.isError && (
        <p role="alert" className="text-sm text-murram">
          {approve.error instanceof ApiError ? approve.error.detail : "Could not publish. Please try again."}
        </p>
      )}
      <Button onClick={() => approve.mutate(insight.id)} disabled={approve.isPending} className="self-start">
        {approve.isPending ? "Publishing…" : "Approve and publish"}
      </Button>
    </li>
  );
}

function PublishedRow({ insight }: { insight: TrendInsight }) {
  return (
    <li className="flex flex-col gap-1 rounded-xl border border-rule bg-page p-4">
      <div className="flex items-center gap-2 text-xs text-soft">
        <Pill tone="leaf">{insight.crop}</Pill>
        <span>{insight.scope_level}</span>
      </div>
      <p className="text-sm text-ink">{insight.message}</p>
      <p className="text-xs text-soft">Approved by {insight.approved_by}</p>
    </li>
  );
}

function TrendsRoute() {
  const pending = useTrends("pending");
  const published = useTrends("published");

  return (
    <div className="flex flex-col gap-4">
      <Card title="Insight approval queue">
        <div className="grid gap-6 lg:grid-cols-2">
          <section className="flex flex-col gap-3">
            <h3 className="text-xs font-semibold uppercase tracking-wide text-soft">Awaiting approval</h3>
            {pending.isLoading ? (
              <p className="text-soft">Loading…</p>
            ) : !pending.data || pending.data.length === 0 ? (
              <EmptyState title="No insights are waiting for approval." />
            ) : (
              <ul className="flex flex-col gap-3">
                {pending.data.map((insight) => (
                  <PendingRow key={insight.id} insight={insight} />
                ))}
              </ul>
            )}
          </section>
          <section className="flex flex-col gap-3">
            <h3 className="text-xs font-semibold uppercase tracking-wide text-soft">Published</h3>
            {published.isLoading ? (
              <p className="text-soft">Loading…</p>
            ) : !published.data || published.data.length === 0 ? (
              <EmptyState title="Nothing has been published yet." />
            ) : (
              <ul className="flex flex-col gap-3">
                {published.data.map((insight) => (
                  <PublishedRow key={insight.id} insight={insight} />
                ))}
              </ul>
            )}
          </section>
        </div>
      </Card>
    </div>
  );
}

export default TrendsRoute;
