import { useQuery } from "@tanstack/react-query";

import { api } from "../../api/client";
import { Icons } from "./Icon";

type ForecastDay = { day: string; icon: "cloud" | "sun" | "rain"; hi: number | null };

export type Weather = {
  place: string;
  temp_c: number;
  summary: string;
  icon: "cloud" | "sun" | "rain";
  humidity: number;
  rain_mm: number;
  wind_kmh: number;
  forecast: ForecastDay[];
};

export function WeatherCard({ parishId }: { parishId?: number }) {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["weather", parishId ?? "default"] as const,
    queryFn: () =>
      api<Weather>(parishId != null ? `/weather/?parish_id=${parishId}` : "/weather/"),
  });

  const place = data?.place ?? "Central Uganda";
  const icon = data?.icon ?? "cloud";
  const Icon = Icons[icon] ?? Icons.cloud;

  return (
    <section id="weather" className="flex scroll-mt-24 flex-col rounded-2xl bg-panel p-5 shadow-[var(--shadow-card)]">
      <h2 className="text-sm font-semibold tracking-wide text-ink">Weather forecast</h2>
      <p className="mt-1 text-xs text-soft">{place}</p>
      {isLoading ? (
        <p className="mt-4 text-sm text-soft">Loading forecast…</p>
      ) : isError || !data ? (
        <p className="mt-4 text-sm text-soft">Weather is unavailable right now.</p>
      ) : (
        <>
          <div className="mt-4 flex items-center gap-3">
            <span className="flex h-12 w-12 items-center justify-center rounded-full bg-leaf/15 text-leaf">
              <Icon className="h-6 w-6" />
            </span>
            <div>
              <p className="tabular text-3xl font-semibold text-ink">{data.temp_c}°</p>
              <p className="text-xs text-soft">{data.summary}</p>
            </div>
          </div>
          <dl className="mt-4 grid grid-cols-3 gap-2 text-center text-xs text-soft">
            <div className="rounded-lg bg-page px-2 py-2">
              <dt>Humidity</dt>
              <dd className="mt-0.5 font-medium text-ink">{data.humidity}%</dd>
            </div>
            <div className="rounded-lg bg-page px-2 py-2">
              <dt>Rain</dt>
              <dd className="mt-0.5 font-medium text-ink">{data.rain_mm} mm</dd>
            </div>
            <div className="rounded-lg bg-page px-2 py-2">
              <dt>Wind</dt>
              <dd className="mt-0.5 font-medium text-ink">{data.wind_kmh} km/h</dd>
            </div>
          </dl>
          <ul className="mt-4 flex justify-between border-t border-rule pt-3">
            {data.forecast.map((d) => {
              const DayIcon = Icons[d.icon] ?? Icons.cloud;
              return (
                <li key={d.day} className="flex flex-col items-center gap-1 text-xs text-soft">
                  <span>{d.day}</span>
                  <DayIcon className="h-4 w-4 text-leaf" />
                  <span className="tabular font-medium text-ink">{d.hi != null ? `${d.hi}°` : "—"}</span>
                </li>
              );
            })}
          </ul>
        </>
      )}
    </section>
  );
}
