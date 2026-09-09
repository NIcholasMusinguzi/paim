import type { DistrictMetric } from "../useNationalMetrics";

type Region = "Northern" | "Eastern" | "Central" | "Western";

const REGION_HINTS: Record<Region, string[]> = {
  Central: ["wakiso", "mukono", "kampala", "mpigi", "masaka", "luwero", "mubende", "kiboga", "mityana"],
  Eastern: ["jinja", "mbale", "tororo", "soroti", "iganga", "kamuli", "bugiri", "palisa"],
  Northern: ["gulu", "lira", "arua", "kitgum", "moroto", "apot", "lamo"],
  Western: ["mbarara", "kabale", "kasese", "hoima", "fort portal", "bundibugyo"],
};

function regionFor(name: string): Region {
  const n = name.toLowerCase();
  for (const [region, hints] of Object.entries(REGION_HINTS) as [Region, string[]][]) {
    if (hints.some((h) => n.includes(h))) return region;
  }
  return "Central";
}

function level(bags: number, max: number): "high" | "medium" | "low" {
  if (max <= 0 || bags <= 0) return "low";
  const ratio = bags / max;
  if (ratio >= 0.66) return "high";
  if (ratio >= 0.33) return "medium";
  return "low";
}

const FILL = { high: "#2f9e44", medium: "#8fd19e", low: "#d5e0d4" };

function UgandaMap({ districts }: { districts: DistrictMetric[] }) {
  const bags: Record<Region, number> = { Northern: 0, Eastern: 0, Central: 0, Western: 0 };
  for (const d of districts) bags[regionFor(d.district)] += d.bags_declared;
  const max = Math.max(...Object.values(bags), 1);

  return (
    <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
      <svg viewBox="0 0 220 260" className="mx-auto h-52 w-auto shrink-0" role="img" aria-label="Uganda production map">
        <ellipse cx="168" cy="210" rx="48" ry="28" fill="#c5e4f3" />
        <path
          d="M78 28c22-14 52-16 74 2 14 12 22 30 28 50 4 16 14 28 28 36 10 6 12 20 4 30-10 12-26 16-36 28-8 10-8 24-4 36 4 10-2 22-12 28-16 10-36 6-52-2-18-10-28-28-34-46-8-24-24-42-28-66-4-22 2-48 16-68 8-12 18-22 16-28z"
          fill={FILL[level(bags.Northern, max)]}
          stroke="#0f3d2e"
          strokeWidth="1.2"
        />
        <path
          d="M148 88c18 8 36 18 42 38 4 14-2 28-14 36-12 8-20 22-16 36 2 10-8 18-20 20l-24-48c-2-18 8-36 32-82z"
          fill={FILL[level(bags.Eastern, max)]}
          stroke="#0f3d2e"
          strokeWidth="1.2"
        />
        <path
          d="M70 118c18-6 40-4 58 10 14 12 18 30 12 46-6 14-4 28 6 38-16 8-36 6-52-4-14-8-24-24-28-40-4-16 0-32 4-50z"
          fill={FILL[level(bags.Central, max)]}
          stroke="#0f3d2e"
          strokeWidth="1.2"
        />
        <path
          d="M42 78c12 18 8 40 4 60-4 18 2 36 14 48-16 4-32-2-40-16-10-18-12-40-6-60 4-14 16-26 28-32z"
          fill={FILL[level(bags.Western, max)]}
          stroke="#0f3d2e"
          strokeWidth="1.2"
        />
      </svg>
      <ul className="flex flex-col gap-1.5 text-xs text-soft">
        <li className="flex items-center gap-2">
          <span className="h-2.5 w-2.5 rounded-full" style={{ background: FILL.high }} /> High production
        </li>
        <li className="flex items-center gap-2">
          <span className="h-2.5 w-2.5 rounded-full" style={{ background: FILL.medium }} /> Medium
        </li>
        <li className="flex items-center gap-2">
          <span className="h-2.5 w-2.5 rounded-full" style={{ background: FILL.low }} /> Low
        </li>
      </ul>
    </div>
  );
}

export default UgandaMap;
