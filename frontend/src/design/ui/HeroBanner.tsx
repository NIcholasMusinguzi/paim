export function HeroBanner({
  title = "PAIM: Smart Information. Better Decisions. Higher Incomes.",
  subtitle,
}: {
  title?: string;
  subtitle?: string;
}) {
  return (
    <div className="relative overflow-hidden rounded-2xl bg-sea px-6 py-8 text-white shadow-[var(--shadow-card)] md:px-10 md:py-10">
      <div className="pointer-events-none absolute inset-y-0 right-0 w-1/2 bg-[radial-gradient(circle_at_70%_50%,rgb(47_158_68/0.45),transparent_60%)]" />
      <svg
        viewBox="0 0 240 160"
        className="pointer-events-none absolute -right-6 bottom-0 hidden h-40 w-auto opacity-90 md:block"
        aria-hidden
      >
        <ellipse cx="170" cy="148" rx="70" ry="10" fill="rgb(0 0 0 / 0.15)" />
        <path d="M40 150c20-40 40-70 55-70 8 0 10 12 6 28-8 28-20 42-40 42H40z" fill="#1b5e38" />
        <path d="M86 86c18-28 48-38 62-20 6 8 2 22-8 32-18 18-40 22-54 10z" fill="#2f9e44" />
        <path d="M130 70c12-22 36-28 48-12 6 8 2 20-8 28-16 14-32 14-40-4z" fill="#8fd19e" />
        <rect x="92" y="86" width="6" height="64" rx="2" fill="#6b4423" />
        <circle cx="188" cy="118" r="22" fill="#e8c547" />
        <circle cx="188" cy="118" r="10" fill="#c08a2e" />
      </svg>
      <div className="relative z-10 max-w-xl">
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-sprout">Parish Agricultural Information</p>
        <h1 className="mt-2 text-2xl font-bold leading-tight md:text-3xl">{title}</h1>
        {subtitle && <p className="mt-2 text-sm text-sprout">{subtitle}</p>}
      </div>
    </div>
  );
}
