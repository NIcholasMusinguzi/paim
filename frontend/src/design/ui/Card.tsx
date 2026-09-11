export function Card({
  title,
  subtitle,
  action,
  className = "",
  children,
  id,
}: {
  title?: string;
  subtitle?: string;
  action?: React.ReactNode;
  className?: string;
  children: React.ReactNode;
  id?: string;
}) {
  return (
    <section id={id} className={`scroll-mt-24 rounded-2xl bg-panel p-5 shadow-[var(--shadow-card)] ${className}`}>
      {(title || action) && (
        <div className="mb-4 flex items-start justify-between gap-3">
          {title && (
            <div>
              <h2 className="text-sm font-semibold tracking-wide text-ink">{title}</h2>
              {subtitle && <p className="mt-1 text-sm font-normal text-soft">{subtitle}</p>}
            </div>
          )}
          {action}
        </div>
      )}
      {children}
    </section>
  );
}
