import { Icons } from "./Icon";

const FORECAST = [
  { day: "Tue", icon: "cloud" as const, hi: 27 },
  { day: "Wed", icon: "sun" as const, hi: 28 },
  { day: "Thu", icon: "rain" as const, hi: 24 },
  { day: "Fri", icon: "cloud" as const, hi: 26 },
  { day: "Sat", icon: "sun" as const, hi: 29 },
];

export function WeatherCard({ place = "Central Uganda" }: { place?: string }) {
  return (
    <section id="weather" className="flex scroll-mt-24 flex-col rounded-2xl bg-panel p-5 shadow-[var(--shadow-card)]">
      <h2 className="text-sm font-semibold tracking-wide text-ink">Weather forecast</h2>
      <p className="mt-1 text-xs text-soft">{place}</p>
      <div className="mt-4 flex items-center gap-3">
        <span className="flex h-12 w-12 items-center justify-center rounded-full bg-leaf/15 text-leaf">
          <Icons.cloud className="h-6 w-6" />
        </span>
        <div>
          <p className="tabular text-3xl font-semibold text-ink">26°</p>
          <p className="text-xs text-soft">Partly cloudy</p>
        </div>
      </div>
      <dl className="mt-4 grid grid-cols-3 gap-2 text-center text-xs text-soft">
        <div className="rounded-lg bg-page px-2 py-2">
          <dt>Humidity</dt>
          <dd className="mt-0.5 font-medium text-ink">62%</dd>
        </div>
        <div className="rounded-lg bg-page px-2 py-2">
          <dt>Rain</dt>
          <dd className="mt-0.5 font-medium text-ink">4 mm</dd>
        </div>
        <div className="rounded-lg bg-page px-2 py-2">
          <dt>Wind</dt>
          <dd className="mt-0.5 font-medium text-ink">12 km/h</dd>
        </div>
      </dl>
      <ul className="mt-4 flex justify-between border-t border-rule pt-3">
        {FORECAST.map((d) => {
          const Icon = Icons[d.icon];
          return (
            <li key={d.day} className="flex flex-col items-center gap-1 text-xs text-soft">
              <span>{d.day}</span>
              <Icon className="h-4 w-4 text-leaf" />
              <span className="tabular font-medium text-ink">{d.hi}°</span>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
