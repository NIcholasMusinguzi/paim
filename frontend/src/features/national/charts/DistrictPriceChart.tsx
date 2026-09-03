import { Bar, BarChart, CartesianGrid, Tooltip, XAxis, YAxis } from "recharts";

import type { DistrictMetric } from "../useNationalMetrics";

// Horizontal bar: comparison across a small set of named categories, labels
// read left to right. Sea for price (IMPLEMENTATION_REACT.md section 6.5).
function DistrictPriceChart({ districts }: { districts: DistrictMetric[] }) {
  const data = districts
    .filter((d) => d.avg_price_per_kg != null)
    .map((d) => ({ district: d.district, price: d.avg_price_per_kg! }));

  return (
    <BarChart width={560} height={Math.max(120, data.length * 36)} data={data} layout="vertical"
      margin={{ left: 16, right: 24 }}>
      <CartesianGrid strokeDasharray="3 3" stroke="var(--color-rule)" horizontal={false} />
      <XAxis type="number" tick={{ fill: "var(--color-soft)", fontSize: 12 }}
        label={{ value: "UGX/kg", position: "insideBottom", offset: -4, fill: "var(--color-soft)", fontSize: 12 }} />
      <YAxis type="category" dataKey="district" width={100} tick={{ fill: "var(--color-ink)", fontSize: 12 }} />
      <Tooltip formatter={(v) => [`UGX ${v}/kg`, "Price"]} />
      <Bar dataKey="price" fill="var(--color-sea)" radius={[0, 3, 3, 0]} />
    </BarChart>
  );
}

export default DistrictPriceChart;
