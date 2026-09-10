import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { api, download } from "../../api/client";
import { useAuth } from "../../app/AuthProvider";
import { Button } from "../../design/ui/Button";
import { Card } from "../../design/ui/Card";
import { EmptyState } from "../../design/ui/EmptyState";
import { Select } from "../../design/ui/Select";

type ParishOpt = { id: number; name: string; district: string; district_id: number };

type Ref = {
  seasons: { id: number; year: number; season_no: number }[];
  crops: { id: number; name: string }[];
};

function districtQuery(district: number | "") {
  return district === "" ? "" : `?district=${district}`;
}

function withDistrict(path: string, district: number | "") {
  if (district === "") return path;
  return `${path}${path.includes("?") ? "&" : "?"}district=${district}`;
}

const SCOPE_COPY: Record<string, string> = {
  national: "All of Uganda",
  district: "Your district",
  subcounty: "Your subcounty",
  parish: "Your parish",
};

function ExportButtons({ path, file }: { path: string; file: string }) {
  const [busy, setBusy] = useState<"xlsx" | "pdf" | null>(null);
  async function run(fmt: "xlsx" | "pdf") {
    setBusy(fmt);
    try {
      await download(`${path}${path.includes("?") ? "&" : "?"}format=${fmt}`, `${file}.${fmt}`);
    } finally {
      setBusy(null);
    }
  }
  return (
    <div className="flex gap-2">
      <Button type="button" variant="secondary" disabled={busy != null} onClick={() => void run("xlsx")}>
        {busy === "xlsx" ? "Exporting…" : "Export Excel"}
      </Button>
      <Button type="button" variant="secondary" disabled={busy != null} onClick={() => void run("pdf")}>
        {busy === "pdf" ? "Exporting…" : "Export PDF"}
      </Button>
    </div>
  );
}

function ReportTable({
  title,
  path,
  file,
  columns,
  rows,
}: {
  title: string;
  path: string;
  file: string;
  columns: { key: string; label: string }[];
  rows: Record<string, unknown>[] | undefined;
}) {
  return (
    <Card title={title} action={<ExportButtons path={path} file={file} />}>
      {!rows || rows.length === 0 ? (
        <EmptyState title="No data in your region for this report." />
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-rule text-xs text-soft">
                {columns.map((col) => (
                  <th key={col.key} className="py-2 pr-3">
                    {col.label}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((row, i) => (
                <tr key={String(row.id ?? i)} className="border-b border-rule">
                  {columns.map((col) => (
                    <td key={col.key} className="py-2 pr-3 text-ink">
                      {row[col.key] == null || row[col.key] === "" ? "—" : String(row[col.key])}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Card>
  );
}

function useReport<T>(path: string, enabled = true) {
  return useQuery({
    queryKey: ["report", path] as const,
    queryFn: () => api<T[]>(path),
    enabled,
  });
}

function ReportsRoute() {
  const { me } = useAuth();
  const { data: ref } = useQuery({
    queryKey: ["reference"] as const,
    queryFn: () => api<Ref>("/reference/"),
    staleTime: 10 * 60_000,
  });
  const { data: parishes } = useQuery({
    queryKey: ["parishes"] as const,
    queryFn: () => api<ParishOpt[]>("/parishes/"),
    staleTime: 10 * 60_000,
  });
  const [season, setSeason] = useState<number | null>(null);
  const [crop, setCrop] = useState<number | null>(null);
  const [district, setDistrict] = useState<number | "">("");

  const districts = (parishes ?? []).reduce<{ id: number; name: string }[]>((acc, p) => {
    if (!acc.some((d) => d.id === p.district_id)) acc.push({ id: p.district_id, name: p.district });
    return acc;
  }, []);

  useEffect(() => {
    if (season == null && ref?.seasons[0]) setSeason(ref.seasons[0].id);
    if (crop == null && ref?.crops[0]) setCrop(ref.crops[0].id);
  }, [ref, season, crop]);

  const qs = season && crop ? `?season=${season}&crop=${crop}` : "";
  const seasonQs = season ? `?season=${season}` : "";
  const ready = Boolean(season && crop);
  const districtQs = districtQuery(district);

  const farmers = useReport<Record<string, unknown>>(`/reports/farmers/${districtQs}`);
  const bids = useReport<Record<string, unknown>>(`/reports/bids/${districtQs}`);
  const prices = useReport<Record<string, unknown>>(`/reports/prices/${qs}`, ready);
  const lots = useReport<Record<string, unknown>>(
    withDistrict(`/reports/lots/${seasonQs}`, district),
    Boolean(season),
  );
  const crops = useReport<Record<string, unknown>>(`/reports/crops/${seasonQs}`, Boolean(season));
  const weather = useReport<Record<string, unknown>>("/reports/weather/");
  const scoped = useReport<Record<string, unknown>>(`/reports/scoped/${qs}`, ready);

  const scopeLabel = me ? SCOPE_COPY[me.scope.level] ?? "Your region" : "Your region";

  return (
    <div className="flex flex-col gap-4">
      <Card title="Report filters">
        <p className="mb-3 text-sm text-soft">{scopeLabel}. National sees every parish; other roles only their area.</p>
        <div className="flex flex-wrap gap-3">
          <Select label="Season" value={season ?? ""} onChange={(e) => setSeason(Number(e.target.value))}>
            {ref?.seasons.map((item) => (
              <option key={item.id} value={item.id}>
                {item.year} season {item.season_no}
              </option>
            ))}
          </Select>
          <Select label="Crop" value={crop ?? ""} onChange={(e) => setCrop(Number(e.target.value))}>
            {ref?.crops.map((item) => (
              <option key={item.id} value={item.id}>
                {item.name}
              </option>
            ))}
          </Select>
          <Select
            label="District"
            value={district}
            onChange={(e) => setDistrict(e.target.value === "" ? "" : Number(e.target.value))}
          >
            <option value="">All districts in your scope</option>
            {districts.map((d) => (
              <option key={d.id} value={d.id}>
                {d.name}
              </option>
            ))}
          </Select>
        </div>
      </Card>

      <ReportTable
        title="Farmers"
        path={`/reports/farmers/${districtQs}`}
        file="paim-farmers"
        columns={[
          { key: "district", label: "District" },
          { key: "subcounty", label: "Subcounty" },
          { key: "parish", label: "Parish" },
          { key: "village", label: "Village" },
          { key: "farmer", label: "Farmer" },
          { key: "sex", label: "Sex" },
          { key: "phone", label: "Phone" },
        ]}
        rows={farmers.data}
      />
      <ReportTable
        title="Bids"
        path={`/reports/bids/${districtQs}`}
        file="paim-bids"
        columns={[
          { key: "district", label: "District" },
          { key: "subcounty", label: "Subcounty" },
          { key: "parish", label: "Parish" },
          { key: "crop", label: "Crop" },
          { key: "lot_status", label: "Lot" },
          { key: "buyer", label: "Buyer" },
          { key: "price_per_kg", label: "UGX/kg" },
          { key: "terms", label: "Terms" },
        ]}
        rows={bids.data}
      />
      <ReportTable
        title="Market prices by crop"
        path={`/reports/prices/${qs}`}
        file="paim-crop-prices"
        columns={[
          { key: "district", label: "District" },
          { key: "subcounty", label: "Subcounty" },
          { key: "parish", label: "Parish" },
          { key: "crop", label: "Crop" },
          { key: "avg_price_per_kg", label: "UGX/kg" },
          { key: "bags_declared", label: "Bags" },
          { key: "pct_grade1", label: "Grade 1" },
        ]}
        rows={prices.data}
      />
      <ReportTable
        title="Lots"
        path={withDistrict(`/reports/lots/${seasonQs}`, district)}
        file="paim-lots"
        columns={[
          { key: "district", label: "District" },
          { key: "subcounty", label: "Subcounty" },
          { key: "parish", label: "Parish" },
          { key: "crop", label: "Crop" },
          { key: "status", label: "Status" },
          { key: "bags", label: "Bags" },
          { key: "bid_count", label: "Bids" },
          { key: "awarded_buyer", label: "Awarded" },
          { key: "awarded_price_per_kg", label: "UGX/kg" },
        ]}
        rows={lots.data}
      />
      <ReportTable
        title="Top crops"
        path={`/reports/crops/${seasonQs}`}
        file="paim-top-crops"
        columns={[
          { key: "crop", label: "Crop" },
          { key: "parishes", label: "Parishes" },
          { key: "bags", label: "Bags" },
          { key: "farmers_active", label: "Active farmers" },
          { key: "avg_price_per_kg", label: "Avg UGX/kg" },
        ]}
        rows={crops.data}
      />
      <ReportTable
        title="Weather insights"
        path="/reports/weather/"
        file="paim-weather-insights"
        columns={[
          { key: "district", label: "District" },
          { key: "subcounty", label: "Subcounty" },
          { key: "parish", label: "Parish" },
          { key: "temp_c", label: "Temp °C" },
          { key: "summary", label: "Summary" },
          { key: "rain_mm", label: "Rain mm" },
          { key: "insight", label: "Insight" },
        ]}
        rows={weather.data}
      />
      <ReportTable
        title="Parish performance"
        path={`/reports/scoped/${qs}`}
        file="paim-parish-performance"
        columns={[
          { key: "district", label: "District" },
          { key: "subcounty", label: "Subcounty" },
          { key: "parish", label: "Parish" },
          { key: "farmers_registered", label: "Farmers" },
          { key: "farmers_active", label: "Active" },
          { key: "bags_declared", label: "Bags" },
          { key: "pct_grade1", label: "Grade 1" },
          { key: "avg_price_per_kg", label: "UGX/kg" },
        ]}
        rows={scoped.data}
      />
    </div>
  );
}

export const Component = ReportsRoute;
export default ReportsRoute;
