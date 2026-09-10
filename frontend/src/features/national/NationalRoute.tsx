import { Suspense, lazy, useEffect, useMemo, useState } from "react";
import { Link } from "react-router";

import { usePosts } from "../../api/hooks/usePosts";
import { useAuth } from "../../app/AuthProvider";
import { formatDateTime, formatInt, formatUgx } from "../../design/format";
import { Card } from "../../design/ui/Card";
import { EmptyState } from "../../design/ui/EmptyState";
import { HeroBanner } from "../../design/ui/HeroBanner";
import { Icons } from "../../design/ui/Icon";
import { Pill } from "../../design/ui/Pill";
import { QuickActions, type QuickAction } from "../../design/ui/QuickActions";
import { Select } from "../../design/ui/Select";
import { StatCard } from "../../design/ui/StatCard";
import { WeatherCard } from "../../design/ui/WeatherCard";
import { useTrends } from "./useTrends";
import { useCropNationalMetrics, useDistrictParishes, useNationalMetrics, useReferenceData } from "./useNationalMetrics";

const DistrictPriceChart = lazy(() => import("./charts/DistrictPriceChart"));
const HarvestDonut = lazy(() => import("./charts/HarvestDonut"));
const UgandaMap = lazy(() => import("./charts/UgandaMap"));

function ParishDrillDown({
  districtId,
  seasonId,
  cropId,
  onClose,
}: {
  districtId: number;
  seasonId: number;
  cropId: number;
  onClose: () => void;
}) {
  const { data: parishes, isLoading } = useDistrictParishes(districtId, seasonId, cropId);

  return (
    <Card title="Parishes" action={<button onClick={onClose} className="text-sm font-medium text-leaf">Close</button>}>
      {isLoading ? (
        <p className="text-soft">Loading…</p>
      ) : !parishes || parishes.length === 0 ? (
        <EmptyState title="No parish figures reported yet for this district." />
      ) : (
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-rule text-left text-xs text-soft">
              <th className="py-2 font-medium">Parish</th>
              <th className="py-2 font-medium">Grade 1</th>
              <th className="py-2 font-medium">UGX/kg</th>
            </tr>
          </thead>
          <tbody>
            {parishes.map((p) => (
              <tr key={p.id} className="border-b border-rule last:border-0">
                <td className="py-2 text-ink">{p.parish}</td>
                <td className="tabular py-2 text-ink">{p.pct_grade1}%</td>
                <td className="tabular py-2 text-ink">{p.avg_price_per_kg ?? "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </Card>
  );
}

const ADMIN_ACTIONS: QuickAction[] = [
  { label: "Add Farmer", to: "/national/admin", icon: "userPlus", tone: "leaf" },
  { label: "Post Advisory", to: "/posts", icon: "megaphone", tone: "sky" },
  { label: "Update Market Price", to: "/national#prices", icon: "tag", tone: "grain" },
  { label: "Register Buyer", to: "/national/admin", icon: "briefcase", tone: "violet" },
  { label: "Bulk Sale", to: "/parish", icon: "truck", tone: "orange" },
  { label: "Generate Report", to: "/reports", icon: "file", tone: "rose" },
];

const DISTRICT_ACTIONS: QuickAction[] = ADMIN_ACTIONS.filter(
  (a) => a.label !== "Add Farmer" && a.label !== "Register Buyer",
);

function NationalRoute() {
  const { me } = useAuth();
  const { data: ref } = useReferenceData();
  const { data: posts } = usePosts();
  const pending = useTrends("pending");
  const published = useTrends("published");
  const [seasonId, setSeasonId] = useState<number | null>(null);
  const [cropId, setCropId] = useState<number | null>(null);
  const [asTable, setAsTable] = useState(false);
  const [drillInto, setDrillInto] = useState<number | null>(null);
  const [advisoryFilter, setAdvisoryFilter] = useState<"all" | "pending" | "published">("all");

  useEffect(() => {
    if (seasonId == null && ref?.seasons.length) setSeasonId(ref.seasons[0].id);
    if (cropId == null && ref?.crops.length) setCropId(ref.crops[0].id);
  }, [ref, seasonId, cropId]);

  const { data, isLoading, isError } = useNationalMetrics(seasonId, cropId);
  const cropQueries = useCropNationalMetrics(seasonId, ref?.crops);

  const cropSeries = useMemo(
    () =>
      (ref?.crops ?? [])
        .map((crop, i) => ({
          name: crop.name,
          districts: cropQueries[i]?.data?.districts ?? [],
          bags: cropQueries[i]?.data?.national?.bags_declared ?? 0,
          price: cropQueries[i]?.data?.national?.avg_price_per_kg ?? null,
        }))
        .filter((s) => s.districts.length > 0 || s.bags > 0 || s.price != null),
    [ref?.crops, cropQueries],
  );

  const selectedCrop = ref?.crops.find((c) => c.id === cropId)?.name;
  const topDistrict = data?.districts[0];
  const insights = [
    ...(advisoryFilter !== "published" ? (pending.data ?? []) : []),
    ...(advisoryFilter !== "pending" ? (published.data ?? []) : []),
  ];

  return (
    <div className="flex flex-col gap-4">
      <HeroBanner subtitle="National view — quality, prices, and aggregation across districts." />

      {!isError && (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <StatCard label="Registered farmers" value={data?.national?.farmers_registered} icon="users" tone="leaf" />
          <StatCard label="Active this season" value={data?.national?.farmers_active} icon="users" tone="sprout" />
          <StatCard label="Districts reporting" value={data?.national?.districts_reporting} icon="grid" tone="sea" />
          <StatCard
            label="Average price"
            value={data?.national?.avg_price_per_kg != null ? formatUgx(data.national.avg_price_per_kg) : "—"}
            icon="tag"
            tone="grain"
            hint={
              selectedCrop && data?.national
                ? `${selectedCrop} · Grade 1 ${data.national.pct_grade1}%`
                : selectedCrop
            }
          />
        </div>
      )}

      <div className="flex flex-wrap items-end gap-3">
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

      {isLoading && <p className="text-soft">Loading…</p>}
      {isError && <EmptyState title="Could not load national figures. Please try again." />}

      <div className="grid gap-4 xl:grid-cols-12">
        <Card title="National overview" className="xl:col-span-5">
          {data?.districts.length ? (
            <div className="flex flex-col gap-4 sm:flex-row">
              <Suspense fallback={<p className="text-sm text-soft">Loading map…</p>}>
                <UgandaMap districts={data.districts} />
              </Suspense>
              <dl className="grid flex-1 grid-cols-2 gap-3 text-sm">
                <div>
                  <dt className="text-xs text-soft">Farmers</dt>
                  <dd className="tabular font-semibold text-ink">{formatInt(data.national?.farmers_registered)}</dd>
                </div>
                <div>
                  <dt className="text-xs text-soft">Bags declared</dt>
                  <dd className="tabular font-semibold text-ink">{formatInt(data.national?.bags_declared)}</dd>
                </div>
                <div>
                  <dt className="text-xs text-soft">Grade 1</dt>
                  <dd className="tabular font-semibold text-ink">{data.national?.pct_grade1 ?? "—"}%</dd>
                </div>
                <div>
                  <dt className="text-xs text-soft">Top district</dt>
                  <dd className="font-semibold text-ink">{topDistrict?.district ?? "—"}</dd>
                </div>
                <div className="col-span-2">
                  <dt className="text-xs text-soft">Top crop</dt>
                  <dd className="font-semibold text-ink">{selectedCrop ?? "—"}</dd>
                </div>
              </dl>
            </div>
          ) : (
            <EmptyState title="No district figures yet for this season and crop." />
          )}
        </Card>

        <Card
          id="prices"
          title="Market prices"
          className="xl:col-span-4"
          action={
            <button onClick={() => setAsTable((v) => !v)} className="text-xs font-medium text-leaf">
              {asTable ? "Chart" : "Table"}
            </button>
          }
        >
          {asTable ? (
            data && data.districts.length > 0 ? (
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-rule text-left text-xs text-soft">
                    <th className="py-2 font-medium">District</th>
                    <th className="py-2 font-medium">UGX/kg</th>
                    <th className="py-2 font-medium">Grade 1</th>
                  </tr>
                </thead>
                <tbody>
                  {data.districts.map((d) => (
                    <tr key={d.id} className="border-b border-rule last:border-0">
                      <td className="py-2">
                        <button onClick={() => setDrillInto(d.district_id)} className="font-medium text-leaf">
                          {d.district}
                        </button>
                      </td>
                      <td className="tabular py-2">{d.avg_price_per_kg ?? "—"}</td>
                      <td className="py-2">
                        <Pill tone={d.pct_grade1 >= 70 ? "leaf" : "grain"}>{d.pct_grade1}%</Pill>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <EmptyState title="No district prices yet." />
            )
          ) : (
            <Suspense fallback={<p className="text-sm text-soft">Loading chart…</p>}>
              {data?.districts ? (
                <DistrictPriceChart districts={data.districts} />
              ) : (
                <p className="text-sm text-soft">Loading chart…</p>
              )}
            </Suspense>
          )}
        </Card>

        <div className="xl:col-span-3">
          <WeatherCard />
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-12">
        <Card
          title="Advisories & guidance"
          className="lg:col-span-4"
          action={
            <div className="flex gap-1 text-xs">
              {(["all", "pending", "published"] as const).map((key) => (
                <button
                  key={key}
                  onClick={() => setAdvisoryFilter(key)}
                  className={`rounded-full px-2.5 py-1 capitalize ${
                    advisoryFilter === key ? "bg-leaf text-white" : "bg-page text-soft"
                  }`}
                >
                  {key}
                </button>
              ))}
            </div>
          }
        >
          {insights.length === 0 ? (
            <EmptyState title="No advisories in this filter." action={<Link to="/national/trends" className="text-sm text-leaf">Insight queue</Link>} />
          ) : (
            <ul className="flex flex-col gap-3">
              {insights.slice(0, 5).map((insight) => (
                <li key={insight.id} className="border-t border-rule pt-3 first:border-0 first:pt-0">
                  <div className="flex items-center gap-2 text-xs text-soft">
                    <Pill tone={insight.published_at ? "leaf" : "grain"}>{insight.crop}</Pill>
                    <span>{insight.scope_level}</span>
                  </div>
                  <p className="mt-1 text-sm text-ink">{insight.message}</p>
                </li>
              ))}
            </ul>
          )}
        </Card>

        <Card id="sales" title="Harvest aggregation" className="lg:col-span-4">
          <Suspense fallback={<p className="text-sm text-soft">Loading…</p>}>
            <HarvestDonut slices={cropSeries.map((s) => ({ name: s.name, value: s.bags }))} />
          </Suspense>
          {data?.national && (
            <p className="mt-3 text-xs text-soft">
              {formatInt(data.national.bags_declared)} bags declared nationally this season.
            </p>
          )}
        </Card>

        <Card title="Current market prices" className="lg:col-span-4">
          {cropSeries.length === 0 ? (
            <EmptyState title="No crop prices yet this season." />
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-rule text-left text-xs text-soft">
                  <th className="py-2 font-medium">Commodity</th>
                  <th className="py-2 font-medium">UGX/kg</th>
                  <th className="py-2 font-medium" />
                </tr>
              </thead>
              <tbody>
                {cropSeries.map((s) => (
                  <tr key={s.name} className="border-b border-rule last:border-0">
                    <td className="py-2 font-medium text-ink">{s.name}</td>
                    <td className="tabular py-2">{s.price ?? "—"}</td>
                    <td className="py-2 text-right text-leaf">
                      <Icons.trendUp className="ml-auto h-4 w-4" />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </Card>
      </div>

      {drillInto != null && seasonId != null && cropId != null && (
        <ParishDrillDown districtId={drillInto} seasonId={seasonId} cropId={cropId} onClose={() => setDrillInto(null)} />
      )}

      <div className="grid gap-4 lg:grid-cols-12">
        <Card
          title="Recent activities"
          className="lg:col-span-8"
          action={
            <Link to="/posts" className="text-sm font-medium text-leaf">
              View all
            </Link>
          }
        >
          {!posts || posts.length === 0 ? (
            <EmptyState title="No recent posts yet." />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-rule text-left text-xs text-soft">
                    <th className="py-2 font-medium">Date & time</th>
                    <th className="py-2 font-medium">Activity</th>
                    <th className="py-2 font-medium">User</th>
                    <th className="py-2 font-medium">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {posts.slice(0, 8).map((p) => (
                    <tr key={p.id} className="border-b border-rule last:border-0">
                      <td className="py-2.5 whitespace-nowrap text-soft">{formatDateTime(p.created_at)}</td>
                      <td className="py-2.5 text-ink">{p.title}</td>
                      <td className="py-2.5 text-ink">{p.author_name}</td>
                      <td className="py-2.5">
                        <Pill tone="leaf">Completed</Pill>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>
        <div className="lg:col-span-4">
          <QuickActions actions={me?.role === "national_admin" ? ADMIN_ACTIONS : DISTRICT_ACTIONS} />
        </div>
      </div>
    </div>
  );
}

export default NationalRoute;
