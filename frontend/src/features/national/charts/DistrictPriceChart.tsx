import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import type { DistrictMetric } from "../useNationalMetrics";

function DistrictPriceChart({
  districts,
  fallback = [],
}: {
  districts: DistrictMetric[];
  fallback?: { name: string; price: number }[];
}) {
  const districtBars = districts
    .filter((d) => d.avg_price_per_kg != null)
    .map((d) => ({ label: d.district, price: d.avg_price_per_kg! }));
  const data =
    districtBars.length > 0
      ? districtBars
      : fallback.map((c) => ({ label: c.name, price: c.price }));

  if (data.length === 0) return <p className="text-sm text-soft">No prices reported yet.</p>;

  return (
    <div className="h-56 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} layout="vertical" margin={{ left: 8, right: 12, top: 4, bottom: 4 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--color-rule)" horizontal={false} />
          <XAxis
            type="number"
            tick={{ fill: "var(--color-soft)", fontSize: 11 }}
            label={{ value: "UGX/kg", position: "insideBottom", offset: -2, fill: "var(--color-soft)", fontSize: 11 }}
          />
          <YAxis type="category" dataKey="label" width={108} tick={{ fill: "var(--color-ink)", fontSize: 11 }} />
          <Tooltip formatter={(v) => [`UGX ${v}/kg`, "Price"]} />
          <Bar dataKey="price" fill="var(--color-leaf)" radius={[0, 6, 6, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export default DistrictPriceChart;
