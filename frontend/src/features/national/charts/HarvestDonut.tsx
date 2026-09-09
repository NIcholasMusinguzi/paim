const COLORS = ["#e0a106", "#2f9e44", "#3b82f6", "#94a3b8", "#0f3d2e"];

function HarvestDonut({ slices }: { slices: { name: string; value: number }[] }) {
  const data = slices.filter((s) => s.value > 0);
  const total = data.reduce((sum, s) => sum + s.value, 0);
  if (total === 0) return <p className="text-sm text-soft">No harvest aggregated yet.</p>;

  const stops: string[] = [];
  let acc = 0;
  data.forEach((s, i) => {
    const start = (acc / total) * 360;
    acc += s.value;
    const end = (acc / total) * 360;
    stops.push(`${COLORS[i % COLORS.length]} ${start}deg ${end}deg`);
  });

  return (
    <div className="flex flex-col items-center gap-3">
      <div
        className="h-36 w-36 rounded-full"
        style={{ background: `conic-gradient(${stops.join(", ")})` }}
        role="img"
        aria-label="Harvest share by crop"
      >
        <div className="m-[22px] flex h-[100px] w-[100px] items-center justify-center rounded-full bg-panel text-center">
          <span className="tabular text-sm font-semibold text-ink">{total} bags</span>
        </div>
      </div>
      <ul className="grid w-full grid-cols-2 gap-x-3 gap-y-1 text-xs">
        {data.map((s, i) => (
          <li key={s.name} className="flex items-center justify-between gap-2">
            <span className="flex items-center gap-1.5 text-soft">
              <span className="h-2 w-2 rounded-full" style={{ background: COLORS[i % COLORS.length] }} />
              {s.name}
            </span>
            <span className="tabular font-medium text-ink">{Math.round((s.value / total) * 100)}%</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default HarvestDonut;
