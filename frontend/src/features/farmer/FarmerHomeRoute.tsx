import { ApiError } from "../../api/client";
import { useLogout } from "../../api/hooks/useMe";
import { Button } from "../../design/ui/Button";
import { EmptyState } from "../../design/ui/EmptyState";
import { Meter } from "../../design/ui/Meter";
import { Pill } from "../../design/ui/Pill";
import { AdviceRequestSection } from "./AdviceRequestSection";
import { PostsSection } from "./PostsSection";
import { useFarmerHome } from "./useFarmerHome";

const GRADE_TONE = { grade_1: "leaf", grade_2: "grain", ungraded: "soft", reject: "murram" } as const;
const LOT_TONE = { open: "grain", closed: "soft", awarded: "leaf", settled: "leaf", cancelled: "murram" } as const;

function tone<T extends string>(map: Record<string, T>, key: string, fallback: T) {
  return map[key] ?? fallback;
}

function FarmerHomeRoute() {
  const logout = useLogout();
  const { data, isLoading, isError, error } = useFarmerHome();

  if (isLoading) return <div className="p-6 text-soft">Loading your home page…</div>;

  if (isError) {
    return (
      <div className="p-6">
        <EmptyState title={error instanceof ApiError ? error.detail : "Something went wrong. Please try again."} />
      </div>
    );
  }

  const home = data!;

  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-6 p-4">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold text-ink">{home.farmer.full_name}</h1>
          <p className="text-sm text-soft">
            {home.farmer.village}, {home.farmer.parish}
          </p>
        </div>
        <Button variant="ghost" onClick={() => logout.mutate()} disabled={logout.isPending}>
          Sign out
        </Button>
      </header>

      <section className="flex flex-col gap-3 rounded-lg bg-panel p-4">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-soft">Advice for you</h2>
        {home.advice.length === 0 ? (
          <EmptyState title="No advice for your crops this week yet." />
        ) : (
          home.advice.map((a) => (
            <div key={a.id} className="border-t border-rule pt-3 first:border-0 first:pt-0">
              <p className="text-sm font-medium text-ink">{a.crop}</p>
              <p className="text-sm text-ink">{a.body}</p>
              <p className="text-xs text-soft">{a.source}</p>
            </div>
          ))
        )}
      </section>

      <section className="flex flex-col gap-4 rounded-lg bg-panel p-4">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-soft">Lot progress</h2>
        {home.lots.length === 0 ? (
          <EmptyState title={`${home.farmer.parish} has not opened a lot this season. Your agent opens it when the first farmer is ready to sell.`} />
        ) : (
          home.lots.map((lot) => (
            <div key={lot.id} className="flex flex-col gap-1">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-ink">{lot.crop}</span>
                <Pill tone={tone(LOT_TONE, lot.status, "soft")}>{lot.status}</Pill>
              </div>
              <Meter value={lot.bags} target={lot.min_bags} label={`${lot.crop} lot`} />
            </div>
          ))
        )}
      </section>

      <section className="flex flex-col gap-3 rounded-lg bg-panel p-4">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-soft">Recent prices</h2>
        {home.prices.length === 0 ? (
          <EmptyState title="No settled prices for your crops yet this season." />
        ) : (
          <ul className="flex flex-col gap-1">
            {home.prices.map((p) => (
              <li key={p.crop} className="flex items-center justify-between text-sm">
                <span className="text-ink">{p.crop}</span>
                <span className="tabular text-ink">UGX {p.avg_price_per_kg}/kg</span>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="flex flex-col gap-3 rounded-lg bg-panel p-4">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-soft">Your recent declarations</h2>
        {home.declarations.length === 0 ? (
          <EmptyState title="You have not declared any harvest yet." />
        ) : (
          <ul className="flex flex-col gap-2">
            {home.declarations.map((d) => (
              <li key={d.id} className="flex items-center justify-between text-sm">
                <span className="text-ink">
                  {d.crop} · {d.bags} bags
                </span>
                <Pill tone={tone(GRADE_TONE, d.grade, "soft")}>{d.grade.replace("_", " ")}</Pill>
              </li>
            ))}
          </ul>
        )}
      </section>

      {home.trends.length > 0 && (
        <section className="flex flex-col gap-3 rounded-lg bg-panel p-4">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-soft">What's changing</h2>
          {home.trends.map((t) => (
            <p key={t.id} className="text-sm text-ink">
              {t.message}
            </p>
          ))}
        </section>
      )}

      <PostsSection />
      <AdviceRequestSection />
    </div>
  );
}

export const Component = FarmerHomeRoute;
