import { useEffect, useState } from "react";

import { api } from "../../api/client";
import { Card } from "../../design/ui/Card";
import { EmptyState } from "../../design/ui/EmptyState";
import { Select } from "../../design/ui/Select";
import { useReferenceData } from "../national/useNationalMetrics";

type ReportRow = {
  id: number;
  parish: string;
  farmers_registered: number;
  farmers_active: number;
  bags_declared: number;
  pct_grade1: number;
  avg_price_per_kg: number | null;
};

export default function ReportsRoute() {
  const { data: ref } = useReferenceData();
  const [season, setSeason] = useState<number | null>(null);
  const [crop, setCrop] = useState<number | null>(null);
  const [rows, setRows] = useState<ReportRow[]>([]);
  useEffect(() => {
    if (season == null && ref?.seasons[0]) setSeason(ref.seasons[0].id);
    if (crop == null && ref?.crops[0]) setCrop(ref.crops[0].id);
  }, [ref, season, crop]);
  useEffect(() => {
    if (season && crop)
      void api<ReportRow[]>(
        `/reports/scoped/?season=${season}&crop=${crop}`,
      ).then(setRows);
  }, [season, crop]);
  return (
    <div className="flex flex-col gap-4">
      <Card title="Scoped report">
        <div className="flex flex-wrap gap-3">
          <Select
            label="Season"
            value={season ?? ""}
            onChange={(e) => setSeason(Number(e.target.value))}
          >
            {ref?.seasons.map((item) => (
              <option key={item.id} value={item.id}>
                {item.year} season {item.season_no}
              </option>
            ))}
          </Select>
          <Select
            label="Crop"
            value={crop ?? ""}
            onChange={(e) => setCrop(Number(e.target.value))}
          >
            {ref?.crops.map((item) => (
              <option key={item.id} value={item.id}>
                {item.name}
              </option>
            ))}
          </Select>
        </div>
      </Card>
      <Card title="Parish performance">
        {rows.length === 0 ? (
          <EmptyState title="No report data for this selection." />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-rule text-xs text-soft">
                  <th className="py-2">Parish</th>
                  <th>Farmers</th>
                  <th>Active</th>
                  <th>Bags</th>
                  <th>Grade 1</th>
                  <th>UGX/kg</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row) => (
                  <tr key={row.id} className="border-b border-rule">
                    <td className="py-2 text-ink">{row.parish}</td>
                    <td>{row.farmers_registered}</td>
                    <td>{row.farmers_active}</td>
                    <td>{row.bags_declared}</td>
                    <td>{row.pct_grade1}%</td>
                    <td>{row.avg_price_per_kg ?? "—"}</td>
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
