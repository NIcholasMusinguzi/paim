import { useEffect, useState } from "react";

import { ApiError } from "../../api/client";
import { useAuth } from "../../app/AuthProvider";
import { EmptyState } from "../../design/ui/EmptyState";
import { LiveBadge } from "../../design/ui/LiveBadge";
import { Meter } from "../../design/ui/Meter";
import { Pill } from "../../design/ui/Pill";
import { Select } from "../../design/ui/Select";
import { useLiveChannel } from "../../realtime/useLiveChannel";
import { AdvisoryQueueSection } from "./AdvisoryQueueSection";
import { PostsSection } from "./PostComposer";
import { useParishDashboard, useParishes } from "./useParishDashboard";

const GRADE_TONE = { grade_1: "leaf", grade_2: "grain", ungraded: "soft", reject: "murram" } as const;

function tone<T extends string>(map: Record<string, T>, key: string, fallback: T) {
  return map[key] ?? fallback;
}

function ParishPicker({ value, onChange }: { value: number | null; onChange: (id: number) => void }) {
  const { data: parishes, isLoading } = useParishes();

  useEffect(() => {
    if (value == null && parishes && parishes.length > 0) onChange(parishes[0].id);
  }, [value, parishes, onChange]);

  if (isLoading) return null;
  if (!parishes || parishes.length === 0) return <EmptyState title="No parishes in your scope." />;
  if (parishes.length === 1) return <h1 className="text-lg font-semibold text-ink">{parishes[0].name}</h1>;

  return (
    <Select label="Parish" value={value ?? ""} onChange={(e) => onChange(Number(e.target.value))}>
      {parishes.map((p) => (
        <option key={p.id} value={p.id}>
          {p.name} · {p.district}
        </option>
      ))}
    </Select>
  );
}

function Dashboard({ parishId }: { parishId: number }) {
  const { data, isLoading, isError, error } = useParishDashboard(parishId);
  const { status, lastEventAt } = useLiveChannel(parishId);

  if (isLoading) return <div className="p-4 text-soft">Loading…</div>;
  if (isError) {
    return <EmptyState title={error instanceof ApiError ? error.detail : "Something went wrong. Please try again."} />;
  }

  const dash = data!;

  return (
    <div className="flex flex-col gap-6">
      <LiveBadge status={status} lastEventAt={lastEventAt} computedAt={dash.metrics?.computed_at} />

      {dash.lot ? (
        <section className="flex flex-col gap-3 rounded-lg bg-panel p-4">
          <div className="flex items-center gap-2">
            <h2 className="text-sm font-semibold uppercase tracking-wide text-soft">{dash.lot.crop} lot</h2>
            <Pill tone="grain">{dash.lot.status}</Pill>
          </div>
          <Meter value={dash.lot.bags} target={dash.lot.min_bags} label={`${dash.lot.crop} lot`} />
        </section>
      ) : (
        <EmptyState title={`${dash.parish.name} has not opened a lot this season. Your agent opens it when the first farmer is ready to sell.`} />
      )}

      {dash.metrics && (
        <section className="grid grid-cols-3 gap-3 rounded-lg bg-panel p-4 text-center">
          <div>
            <p className="tabular text-figure text-ink">{dash.metrics.pct_grade1}%</p>
            <p className="text-xs text-soft">Grade 1</p>
          </div>
          <div>
            <p className="tabular text-figure text-ink">{dash.metrics.farmers_active}</p>
            <p className="text-xs text-soft">Active farmers</p>
          </div>
          <div>
            <p className="tabular text-figure text-ink">
              {dash.metrics.avg_price_per_kg != null ? `${dash.metrics.avg_price_per_kg}` : "—"}
            </p>
            <p className="text-xs text-soft">UGX/kg</p>
          </div>
        </section>
      )}

      <section className="flex flex-col gap-3 rounded-lg bg-panel p-4">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-soft">Declarations</h2>
        {dash.declarations.length === 0 ? (
          <EmptyState title="No declarations for this lot yet." />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-rule text-left text-xs text-soft">
                  <th className="py-1 font-medium">Farmer</th>
                  <th className="py-1 font-medium">Bags</th>
                  <th className="py-1 font-medium">Grade</th>
                </tr>
              </thead>
              <tbody>
                {dash.declarations.map((d) => (
                  <tr key={d.id} className="border-b border-rule last:border-0">
                    <td className="py-1.5 text-ink">{d.farmer_name}</td>
                    <td className="tabular py-1.5 text-ink">{d.bags}</td>
                    <td className="py-1.5">
                      <Pill tone={tone(GRADE_TONE, d.grade, "soft")}>{d.grade.replace("_", " ")}</Pill>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}

function OfficerRoute() {
  const { me } = useAuth();
  const [parishId, setParishId] = useState<number | null>(
    me?.scope.level === "parish" ? me.scope.id : null,
  );

  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-4 p-4">
      <ParishPicker value={parishId} onChange={setParishId} />
      {parishId != null && <Dashboard parishId={parishId} />}
      <AdvisoryQueueSection />
      <PostsSection />
    </div>
  );
}

export const Component = OfficerRoute;
