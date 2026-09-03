import type { LiveStatus } from "../../realtime/useLiveChannel";

function formatAgo(date: Date | string): string {
  const ms = Date.now() - +new Date(date);
  const s = Math.round(ms / 1000);
  if (s < 5) return "just now";
  if (s < 60) return `${s}s ago`;
  const m = Math.round(s / 60);
  if (m < 60) return `${m}m ago`;
  return `${Math.round(m / 60)}h ago`;
}

const STALE_MS = 36 * 3600_000;

export function LiveBadge({
  status,
  lastEventAt,
  computedAt,
}: {
  status: LiveStatus;
  lastEventAt: Date | null;
  computedAt?: string | null;
}) {
  const stale = computedAt != null && Date.now() - +new Date(computedAt) > STALE_MS;

  if (stale) {
    return (
      <div role="status" className="rounded border border-murram bg-murram/10 px-3 py-2 text-sm text-murram">
        Figures last calculated {formatAgo(computedAt!)}. Declarations made since are not included.
      </div>
    );
  }

  const tone = status === "open" ? "bg-leaf" : status === "reconnecting" ? "bg-grain" : "bg-murram";

  return (
    <span aria-live="polite" className="inline-flex items-center gap-2 text-xs text-soft">
      <span className={`h-2 w-2 rounded-full ${tone} ${status === "open" ? "animate-pulse" : ""}`} />
      {status === "open" && (lastEventAt ? `Live · updated ${formatAgo(lastEventAt)}` : "Live")}
      {status === "connecting" && "Connecting…"}
      {status === "reconnecting" && "Reconnecting — figures may be behind"}
      {status === "offline" && "Not live — showing the last figures loaded"}
    </span>
  );
}
