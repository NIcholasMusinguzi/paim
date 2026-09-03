export function Meter({ value, target, label }: { value: number; target: number; label: string }) {
  const pct = target > 0 ? Math.min(100, Math.round((value / target) * 100)) : 0;
  return (
    <div className="flex flex-col gap-1">
      <div className="flex items-baseline justify-between text-sm">
        <span className="text-soft">{label}</span>
        <span className="tabular text-ink">
          {value} / {target} bags
        </span>
      </div>
      <div
        role="progressbar"
        aria-valuenow={value}
        aria-valuemin={0}
        aria-valuemax={target}
        aria-label={label}
        className="h-3 overflow-hidden rounded-full bg-rule"
      >
        <div
          className="h-full rounded-full bg-grain transition-[width] duration-300 motion-reduce:transition-none"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}
