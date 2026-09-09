import { formatInt } from "../format";
import { Icons, type IconName } from "./Icon";

const ICON_TONE: Record<string, string> = {
  leaf: "bg-leaf/15 text-leaf",
  sea: "bg-sea/10 text-sea",
  grain: "bg-grain/15 text-grain",
  sprout: "bg-sprout/40 text-sea",
};

export function StatCard({
  label,
  value,
  icon,
  tone = "leaf",
  hint,
}: {
  label: string;
  value: number | string | null | undefined;
  icon: IconName;
  tone?: keyof typeof ICON_TONE;
  hint?: string;
}) {
  const Icon = Icons[icon];
  const display = typeof value === "number" ? formatInt(value) : (value ?? "—");
  return (
    <div className="flex items-center gap-4 rounded-2xl bg-panel p-4 shadow-[var(--shadow-card)]">
      <span className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-full ${ICON_TONE[tone]}`}>
        <Icon className="h-5 w-5" />
      </span>
      <div className="min-w-0">
        <p className="tabular text-2xl font-semibold tracking-tight text-ink">{display}</p>
        <p className="text-xs font-medium text-soft">{label}</p>
        {hint && <p className="mt-0.5 text-xs text-leaf">{hint}</p>}
      </div>
    </div>
  );
}
