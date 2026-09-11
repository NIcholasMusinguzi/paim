import { useEffect, useState } from "react";

import { ApiError } from "../../api/client";
import { useMarketPrices } from "../../api/hooks/useMarketPrices";
import { useAuth } from "../../app/AuthProvider";
import { formatInt, formatUgx } from "../../design/format";
import { Card } from "../../design/ui/Card";
import { EmptyState } from "../../design/ui/EmptyState";
import { HeroBanner } from "../../design/ui/HeroBanner";
import { LiveBadge } from "../../design/ui/LiveBadge";
import { Meter } from "../../design/ui/Meter";
import { Pill } from "../../design/ui/Pill";
import { QuickActions } from "../../design/ui/QuickActions";
import { Select } from "../../design/ui/Select";
import { StatCard } from "../../design/ui/StatCard";
import { WeatherCard } from "../../design/ui/WeatherCard";
import { useLiveChannel } from "../../realtime/useLiveChannel";
import { useParishDashboard, useParishes } from "./useParishDashboard";

const GRADE_TONE = {
  grade_1: "leaf",
  grade_2: "grain",
  ungraded: "soft",
  reject: "murram",
} as const;

function tone<T extends string>(
  map: Record<string, T>,
  key: string,
  fallback: T,
) {
  return map[key] ?? fallback;
}

function ParishPicker({
  value,
  onChange,
}: {
  value: number | null;
  onChange: (id: number) => void;
}) {
  const { data: parishes, isLoading } = useParishes();

  useEffect(() => {
    if (value == null && parishes && parishes.length > 0)
      onChange(parishes[0].id);
  }, [value, parishes, onChange]);

  if (isLoading) return null;
  if (!parishes || parishes.length === 0)
    return <EmptyState title="No parishes in your scope." />;
  if (parishes.length === 1) {
    return (
      <p className="text-sm font-medium text-ink">
        {parishes[0].name} · {parishes[0].district}
      </p>
    );
  }

  return (
    <Select
      label="Parish"
      value={value ?? ""}
      onChange={(e) => onChange(Number(e.target.value))}
    >
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
  const { data: marketPrices } = useMarketPrices();

  if (isLoading) return <div className="text-soft">Loading…</div>;
  if (isError) {
    return (
      <EmptyState
        title={
          error instanceof ApiError
            ? error.detail
            : "Something went wrong. Please try again."
        }
      />
    );
  }

  const dash = data!;
  const producePrices = (marketPrices ?? []).filter((p) => p.category === "produce");
  const listedPrice = producePrices.find((p) => p.item_name === dash.lot?.crop);
  const avgPrice = dash.metrics?.avg_price_per_kg ?? listedPrice?.price ?? null;

  return (
    <div className="flex flex-col gap-4">
      <LiveBadge
        status={status}
        lastEventAt={lastEventAt}
        computedAt={dash.metrics?.computed_at}
      />

      {dash.metrics && (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <StatCard
            label="Active farmers"
            value={dash.metrics.farmers_active}
            icon="users"
            tone="leaf"
          />
          <StatCard
            label="Bags declared"
            value={dash.metrics.bags_declared}
            icon="truck"
            tone="sprout"
          />
          <StatCard
            label="Grade 1"
            value={`${dash.metrics.pct_grade1}%`}
            icon="grid"
            tone="sea"
          />
          <StatCard
            label="Average price"
            value={avgPrice != null ? formatUgx(avgPrice) : "—"}
            icon="tag"
            tone="grain"
          />
        </div>
      )}

      <div className="grid gap-4 xl:grid-cols-12">
        <Card title="Parish overview" className="xl:col-span-5">
          <dl className="grid grid-cols-2 gap-3 text-sm">
            <div>
              <dt className="text-xs text-soft">Parish</dt>
              <dd className="font-semibold text-ink">{dash.parish.name}</dd>
            </div>
            <div>
              <dt className="text-xs text-soft">District</dt>
              <dd className="font-semibold text-ink">{dash.parish.district}</dd>
            </div>
            <div>
              <dt className="text-xs text-soft">Farmers active</dt>
              <dd className="tabular font-semibold text-ink">
                {dash.metrics?.farmers_active ?? "—"}
              </dd>
            </div>
            <div>
              <dt className="text-xs text-soft">Top crop</dt>
              <dd className="font-semibold text-ink">
                {dash.lot?.crop ?? "—"}
              </dd>
            </div>
          </dl>
        </Card>

        <Card
          id="sales"
          title="Harvest aggregation & sales"
          className="xl:col-span-4"
        >
          {dash.lot ? (
            <div className="flex flex-col gap-3">
              <div className="flex items-center gap-2">
                <h3 className="text-sm font-medium text-ink">
                  {dash.lot.crop} lot
                </h3>
                <Pill tone="grain">{dash.lot.status}</Pill>
              </div>
              <Meter
                value={dash.lot.bags}
                target={dash.lot.min_bags}
                label={`${dash.lot.crop} lot`}
              />
              <p className="text-xs text-soft">
                Next bulk sale opens when the lot reaches {dash.lot.min_bags}{" "}
                bags.
              </p>
            </div>
          ) : (
            <EmptyState
              title={`${dash.parish.name} has not opened a lot this season. Your agent opens it when the first farmer is ready to sell.`}
            />
          )}
        </Card>

        <div className="xl:col-span-3">
          <WeatherCard parishId={parishId} />
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-12">
        <Card
          id="prices"
          title="Current market prices"
          className="lg:col-span-12"
        >
          {dash.metrics?.avg_price_per_kg != null && dash.lot ? (
            <div className="flex items-center justify-between text-sm">
              <span className="font-medium text-ink">{dash.lot.crop}</span>
              <span className="tabular text-ink">
                {formatUgx(dash.metrics.avg_price_per_kg)}/kg
              </span>
            </div>
          ) : producePrices.length > 0 ? (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-rule text-left text-xs text-soft">
                  <th className="py-2 font-medium">Commodity</th>
                  <th className="py-2 font-medium">UGX/kg</th>
                </tr>
              </thead>
              <tbody>
                {producePrices.map((p) => (
                  <tr key={p.id} className="border-b border-rule last:border-0">
                    <td className="py-2 font-medium text-ink">{p.item_name}</td>
                    <td className="tabular py-2">{formatInt(p.price)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <EmptyState title="No settled price for this parish yet." />
          )}
        </Card>
      </div>

      <Card title="Declarations">
        {dash.declarations.length === 0 ? (
          <EmptyState title="No declarations for this lot yet." />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-rule text-left text-xs text-soft">
                  <th className="py-2 font-medium">Farmer</th>
                  <th className="py-2 font-medium">Bags</th>
                  <th className="py-2 font-medium">Grade</th>
                </tr>
              </thead>
              <tbody>
                {dash.declarations.map((d) => (
                  <tr key={d.id} className="border-b border-rule last:border-0">
                    <td className="py-2.5 text-ink">{d.farmer_name}</td>
                    <td className="tabular py-2.5 text-ink">{d.bags}</td>
                    <td className="py-2.5">
                      <Pill tone={tone(GRADE_TONE, d.grade, "soft")}>
                        {d.grade.replace("_", " ")}
                      </Pill>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}

function OfficerRoute() {
  const { me } = useAuth();
  const [parishId, setParishId] = useState<number | null>(
    me?.scope.level === "parish" ? me.scope.id : null,
  );

  return (
    <div className="flex flex-col gap-4">
      <HeroBanner subtitle="Parish view — lots, advisories, and farmer declarations." />
      <ParishPicker value={parishId} onChange={setParishId} />
      {parishId != null && <Dashboard parishId={parishId} />}
      <QuickActions
        actions={[
          {
            label: "Post Advisory",
            to: "/posts",
            icon: "megaphone",
            tone: "sky",
          },
          {
            label: "Bulk Sale",
            to: "/parish#sales",
            icon: "truck",
            tone: "orange",
          },
          {
            label: "Update Market Price",
            to: "/parish#prices",
            icon: "tag",
            tone: "grain",
          },
        ]}
      />
    </div>
  );
}

export default OfficerRoute;
