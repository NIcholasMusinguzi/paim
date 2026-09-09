export function Card({
  title,
  action,
  className = "",
  children,
  id,
}: {
  title?: string;
  action?: React.ReactNode;
  className?: string;
  children: React.ReactNode;
  id?: string;
}) {
  return (
    <section id={id} className={`scroll-mt-24 rounded-2xl bg-panel p-5 shadow-[var(--shadow-card)] ${className}`}>
      {(title || action) && (
        <div className="mb-4 flex items-center justify-between gap-3">
          {title && <h2 className="text-sm font-semibold tracking-wide text-ink">{title}</h2>}
          {action}
        </div>
      )}
      {children}
    </section>
  );
}
