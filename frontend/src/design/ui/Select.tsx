import { type SelectHTMLAttributes, forwardRef, useId } from "react";

type Props = SelectHTMLAttributes<HTMLSelectElement> & { label: string; children: React.ReactNode };

export const Select = forwardRef<HTMLSelectElement, Props>(({ label, id, className = "", children, ...props }, ref) => {
  const autoId = useId();
  const fieldId = id ?? autoId;
  return (
    <div className="flex flex-col gap-1">
      <label htmlFor={fieldId} className="text-sm font-medium text-ink">
        {label}
      </label>
      <select
        ref={ref}
        id={fieldId}
        className={`min-h-11 rounded border border-rule bg-panel px-3 py-2 text-ink outline-none focus:border-sea ${className}`}
        {...props}
      >
        {children}
      </select>
    </div>
  );
});
Select.displayName = "Select";
