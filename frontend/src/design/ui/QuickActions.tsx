import { Link } from "react-router";

import { Icons, type IconName } from "./Icon";

export type QuickAction = {
  label: string;
  to: string;
  icon: IconName;
  tone: "leaf" | "sky" | "grain" | "violet" | "orange" | "rose";
};

const TONE: Record<QuickAction["tone"], string> = {
  leaf: "bg-leaf/10 text-leaf hover:bg-leaf/20",
  sky: "bg-sky-100 text-sky-700 hover:bg-sky-200",
  grain: "bg-grain/15 text-amber-800 hover:bg-grain/25",
  violet: "bg-violet-100 text-violet-700 hover:bg-violet-200",
  orange: "bg-orange-100 text-orange-700 hover:bg-orange-200",
  rose: "bg-rose-100 text-rose-700 hover:bg-rose-200",
};

export function QuickActions({ actions }: { actions: QuickAction[] }) {
  return (
    <section className="rounded-2xl bg-panel p-5 shadow-[var(--shadow-card)]">
      <h2 className="mb-4 text-sm font-semibold tracking-wide text-ink">Quick actions</h2>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
        {actions.map((a) => {
          const Icon = Icons[a.icon];
          return (
            <Link
              key={a.label}
              to={a.to}
              className={`flex min-h-24 flex-col items-center justify-center gap-2 rounded-xl px-3 py-4 text-center text-xs font-semibold transition-colors ${TONE[a.tone]}`}
            >
              <Icon className="h-6 w-6" />
              {a.label}
            </Link>
          );
        })}
      </div>
    </section>
  );
}
