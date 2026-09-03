export function EmptyState({ title, action }: { title: string; action?: React.ReactNode }) {
  return (
    <div className="flex flex-col items-center gap-3 rounded border border-dashed border-rule bg-panel p-8 text-center">
      <p className="text-soft">{title}</p>
      {action}
    </div>
  );
}
