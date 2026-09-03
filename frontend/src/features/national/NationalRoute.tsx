import { Suspense, lazy, useEffect, useState } from "react";
import { Link } from "react-router";

import { EmptyState } from "../../design/ui/EmptyState";
import { Pill } from "../../design/ui/Pill";
import { Select } from "../../design/ui/Select";
import { useDistrictParishes, useNationalMetrics, useReferenceData } from "./useNationalMetrics";

const DistrictPriceChart = lazy(() => import("./charts/DistrictPriceChart")); // separate chunk

function ParishDrillDown({ districtId, seasonId, cropId, onClose }: {
  districtId: number; seasonId: number; cropId: number; onClose: () => void;
}) {
  const { data: parishes, isLoading } = useDistrictParishes(districtId, seasonId, cropId);

  return (
    <div className="flex flex-col gap-3 rounded-lg bg-panel p-4">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-soft">Parishes</h2>
        <button onClick={onClose} className="text-sm text-sea underline">
          Close
        </button>
      </div>
      {isLoading ? (
        <p className="text-soft">Loading…</p>
      ) : !parishes || parishes.length === 0 ? (
        <EmptyState title="No parish figures reported yet for this district." />
      ) : (
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-rule text-left text-xs text-soft">
              <th className="py-1 font-medium">Parish</th>
              <th className="py-1 font-medium">Grade 1</th>
              <th className="py-1 font-medium">UGX/kg</th>
            </tr>
          </thead>
          <tbody>
            {parishes.map((p) => (
              <tr key={p.id} className="border-b border-rule last:border-0">
                <td className="py-1.5 text-ink">{p.parish}</td>
                <td className="tabular py-1.5 text-ink">{p.pct_grade1}%</td>
                <td className="tabular py-1.5 text-ink">{p.avg_price_per_kg ?? "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

function NationalRoute() {
  const { data: ref } = useReferenceData();
  const [seasonId, setSeasonId] = useState<number | null>(null);
  const [cropId, setCropId] = useState<number | null>(null);
  const [asTable, setAsTable] = useState(false);
  const [drillInto, setDrillInto] = useState<number | null>(null);

  useEffect(() => {
    if (seasonId == null && ref?.seasons.length) setSeasonId(ref.seasons[0].id);
    if (cropId == null && ref?.crops.length) setCropId(ref.crops[0].id);
  }, [ref, seasonId, cropId]);

  const { data, isLoading, isError } = useNationalMetrics(seasonId, cropId);

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-4 p-4">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-semibold text-ink">National dashboard</h1>
        <Link to="/national/trends" className="text-sm text-sea underline">
          Insight queue
        </Link>
      </div>

      <div className="flex gap-3">
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

      {data?.national && (
        <section className="grid grid-cols-3 gap-3 rounded-lg bg-panel p-4 text-center">
          <div>
            <p className="tabular text-figure text-ink">{data.national.pct_grade1}%</p>
            <p className="text-xs text-soft">Grade 1</p>
          </div>
          <div>
            <p className="tabular text-figure text-ink">{data.national.bags_declared}</p>
            <p className="text-xs text-soft">Bags declared</p>
          </div>
          <div>
            <p className="tabular text-figure text-ink">
              {data.national.avg_price_per_kg != null ? data.national.avg_price_per_kg : "—"}
            </p>
            <p className="text-xs text-soft">UGX/kg</p>
          </div>
        </section>
      )}

      {data && data.districts.length > 0 && (
        <section className="flex flex-col gap-3 rounded-lg bg-panel p-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold uppercase tracking-wide text-soft">Districts by price</h2>
            <button onClick={() => setAsTable((v) => !v)} className="text-sm text-sea underline">
              {asTable ? "View as chart" : "View as table"}
            </button>
          </div>

          {asTable ? (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-rule text-left text-xs text-soft">
                  <th className="py-1 font-medium">Rank</th>
                  <th className="py-1 font-medium">District</th>
                  <th className="py-1 font-medium">UGX/kg</th>
                  <th className="py-1 font-medium">Grade 1</th>
                </tr>
              </thead>
              <tbody>
                {data.districts.map((d) => (
                  <tr key={d.id} className="border-b border-rule last:border-0">
                    <td className="tabular py-1.5 text-ink">{d.rank_national ?? "—"}</td>
                    <td className="py-1.5 text-ink">
                      <button onClick={() => setDrillInto(d.district_id)} className="text-sea underline">
                        {d.district}
                      </button>
                    </td>
                    <td className="tabular py-1.5 text-ink">{d.avg_price_per_kg ?? "—"}</td>
                    <td className="py-1.5">
                      <Pill tone={d.pct_grade1 >= 70 ? "leaf" : "grain"}>{d.pct_grade1}%</Pill>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <Suspense fallback={<p className="text-soft">Loading chart…</p>}>
              <DistrictPriceChart districts={data.districts} />
            </Suspense>
          )}
        </section>
      )}

      {drillInto != null && seasonId != null && cropId != null && (
        <ParishDrillDown districtId={drillInto} seasonId={seasonId} cropId={cropId} onClose={() => setDrillInto(null)} />
      )}
    </div>
  );
}

export default NationalRoute;
