import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router";
import { useQuery } from "@tanstack/react-query";

import { api } from "../../api/client";
import { useAuth } from "../../app/AuthProvider";
import { formatInt, formatUgx } from "../../design/format";
import { Card } from "../../design/ui/Card";
import { EmptyState } from "../../design/ui/EmptyState";
import { HeroBanner } from "../../design/ui/HeroBanner";
import { Pill } from "../../design/ui/Pill";
import { Select } from "../../design/ui/Select";
import { type TrendInsight, useTrends } from "../national/useTrends";
import {
  useDistrictParishes,
  useDistrictSeasonBars,
  useReferenceData,
} from "../national/useNationalMetrics";

type ParishOpt = { id: number; name: string; district: string; district_id: number };

const METRIC_LABEL: Record<string, string> = {
  avg_price_per_kg: "Price after peak harvest",
  pct_grade1: "Grade 1 share",
  moisture_pct: "Moisture at declaration",
};

function gradeTone(pct: number): "leaf" | "grain" | "murram" {
  if (pct >= 70) return "leaf";
  if (pct >= 50) return "grain";
  return "murram";
}

function InsightsRoute() {
  const { me } = useAuth();
  const { data: ref } = useReferenceData();
  const parishes = useQuery({
    queryKey: ["parishes"] as const,
    queryFn: () => api<ParishOpt[]>("/parishes/"),
  });
  const pending = useTrends("pending");
  const published = useTrends("published");
  const [seasonId, setSeasonId] = useState<number | null>(null);
  const [cropId, setCropId] = useState<number | null>(null);
  const [districtId, setDistrictId] = useState<number | null>(null);

  const districts = useMemo(() => {
    const seen = new Map<number, string>();
    for (const parish of parishes.data ?? []) {
      if (!seen.has(parish.district_id)) seen.set(parish.district_id, parish.district);
    }
    return [...seen.entries()].map(([id, name]) => ({ id, name }));
  }, [parishes.data]);

  useEffect(() => {
    if (seasonId == null && ref?.seasons.length) setSeasonId(ref.seasons[0].id);
    if (cropId == null && ref?.crops.length) setCropId(ref.crops[0].id);
    if (districtId == null && districts.length) setDistrictId(districts[0].id);
  }, [ref, seasonId, cropId, districtId, districts]);

  const comparison = useDistrictParishes(districtId, seasonId, cropId);
  const bars = useDistrictSeasonBars(districtId, cropId);
  const districtName = districts.find((d) => d.id === districtId)?.name ?? "your district";
  const insights: TrendInsight[] = [...(published.data ?? []), ...(pending.data ?? [])];
  const canApprove = me?.role === "national_admin" || me?.role === "district_officer";

  return (
    <div className="mx-auto flex max-w-5xl flex-col gap-4">
      <HeroBanner subtitle="Parishes compared within a district, and the trend layer that turns those numbers into guidance." />

      <Card>
        <div className="flex flex-wrap items-end gap-3">
          <Select
            label="District"
            value={districtId ?? ""}
            onChange={(e) => setDistrictId(Number(e.target.value))}
          >
            {districts.map((d) => (
              <option key={d.id} value={d.id}>
                {d.name}
              </option>
            ))}
          </Select>
          <Select label="Season" value={seasonId ?? ""} onChange={(e) => setSeasonId(Number(e.target.value))}>
            {ref?.seasons.map((s) => (
              <option key={s.id} value={s.id}>
                {s.year} season {s.season_no}
              </option>
            ))}
          </Select>
          <Select label="Crop" value={cropId ?? ""} onChange={(e) => setCropId(Number(e.target.value))}>
            {ref?.crops.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </Select>
        </div>
      </Card>

      <Card
        title={`Parishes in ${districtName}`}
        subtitle="Parish is the unit that acts, so it is the unit that is measured."
      >
        {comparison.isLoading ? (
          <p className="text-sm text-soft">Loading…</p>
        ) : !comparison.data || comparison.data.length === 0 ? (
          <EmptyState title="No parishes in this district yet." />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-rule text-left text-xs text-soft">
                  <th className="py-2 pr-3 font-medium">Parish</th>
                  <th className="py-2 pr-3 font-medium">Farmers</th>
                  <th className="py-2 pr-3 font-medium">Active</th>
                  <th className="py-2 pr-3 font-medium">Bags</th>
                  <th className="py-2 pr-3 font-medium">Grade 1</th>
                  <th className="py-2 pr-3 font-medium">UGX/kg</th>
                  <th className="py-2 font-medium">Agent reach</th>
                </tr>
              </thead>
              <tbody>
                {comparison.data.map((row) => (
                  <tr key={row.parish_id} className="border-b border-rule last:border-0">
                    <td className="py-2.5 pr-3">
                      <span className="font-medium text-ink">{row.parish}</span>
                      {row.live && (
                        <span className="ml-2">
                          <Pill tone="soft">live</Pill>
                        </span>
                      )}
                    </td>
                    <td className="tabular py-2.5 pr-3 text-ink">{formatInt(row.farmers_registered)}</td>
                    <td className="tabular py-2.5 pr-3 text-ink">{formatInt(row.farmers_active)}</td>
                    <td className="tabular py-2.5 pr-3 text-ink">{formatInt(row.bags_declared)}</td>
                    <td className="py-2.5 pr-3">
                      <Pill tone={gradeTone(row.pct_grade1)}>{row.pct_grade1}%</Pill>
                    </td>
                    <td className="tabular py-2.5 pr-3 text-ink">
                      {row.avg_price_per_kg != null ? formatInt(row.avg_price_per_kg) : "—"}
                    </td>
                    <td className="tabular py-2.5 text-ink">{row.agent_reach}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      <Card
        title="Trends and the guidance they generate"
        subtitle="An insight is only sent to farmers once an officer approves it. Approval is recorded against the insight."
        action={
          canApprove ? (
            <Link to="/national/trends" className="text-sm font-medium text-leaf">
              Insight queue
            </Link>
          ) : undefined
        }
      >
        <h3 className="text-xs font-semibold uppercase tracking-wide text-soft">
          Grade 1 share and mean price, last three seasons
        </h3>
        {!bars.data || bars.data.length === 0 ? (
          <EmptyState title="Not enough seasons yet to draw a trend." />
        ) : (
          <ul className="mt-3 flex flex-col gap-3">
            {bars.data.map((bar) => (
              <li key={bar.season_id} className="flex items-center gap-3">
                <div className="w-28 shrink-0 text-sm">
                  <p className="font-medium text-ink">{bar.label}</p>
                  <p className="text-xs text-soft">{bar.pct_grade1}% grade 1</p>
                </div>
                <div className="h-6 flex-1 overflow-hidden rounded bg-page">
                  <div
                    className="h-6 rounded bg-grain"
                    style={{ width: `${Math.max(bar.pct_grade1, 4)}%` }}
                  />
                </div>
                <p className="w-24 shrink-0 text-right text-sm text-soft">
                  {bar.avg_price_per_kg != null ? formatUgx(bar.avg_price_per_kg) : "—"}
                </p>
              </li>
            ))}
          </ul>
        )}

        <h3 className="mt-6 text-xs font-semibold uppercase tracking-wide text-soft">
          Insights generated from this data
        </h3>
        {insights.length === 0 ? (
          <EmptyState title="No insights have been drafted for your area yet." />
        ) : (
          <ul className="mt-3 flex flex-col gap-4">
            {insights.map((insight) => {
              const published = Boolean(insight.published_at);
              return (
                <li
                  key={insight.id}
                  className={`border-l-4 pl-3 ${published ? "border-leaf" : "border-murram"}`}
                >
                  <p className="text-sm text-ink">{insight.message}</p>
                  <p className="mt-1 text-xs text-soft">
                    {insight.scope_name ?? insight.scope_level} · {insight.crop} ·{" "}
                    {METRIC_LABEL[insight.metric] ?? insight.metric}
                    {" · "}
                    {published
                      ? `published${insight.approved_by ? ` by ${insight.approved_by}` : ""}`
                      : "awaiting approval"}
                  </p>
                </li>
              );
            })}
          </ul>
        )}
      </Card>
    </div>
  );
}

export const Component = InsightsRoute;
