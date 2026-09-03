export interface ResourceColumn<T> {
  key: string;
  label: string;
  render?: (row: T) => React.ReactNode;
}

export function ResourceTable<T extends { id: number }>({
  columns,
  rows,
  onEdit,
  onDelete,
  deleting,
}: {
  columns: ResourceColumn<T>[];
  rows: T[];
  onEdit: (row: T) => void;
  onDelete?: (id: number) => void;
  deleting?: boolean;
}) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-rule text-left text-xs text-soft">
            {columns.map((c) => (
              <th key={c.key} className="py-1 pr-3 font-medium">
                {c.label}
              </th>
            ))}
            <th />
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.id} className="border-b border-rule last:border-0">
              {columns.map((c) => (
                <td key={c.key} className="py-1.5 pr-3 text-ink">
                  {c.render ? c.render(row) : String((row as Record<string, unknown>)[c.key] ?? "—")}
                </td>
              ))}
              <td className="py-1.5 text-right whitespace-nowrap">
                <button onClick={() => onEdit(row)} className="mr-3 text-xs text-sea underline">
                  Edit
                </button>
                {onDelete && (
                  <button onClick={() => onDelete(row.id)} disabled={deleting} className="text-xs text-murram underline">
                    Delete
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
