import { type InputHTMLAttributes, forwardRef, useId } from "react";

type Props = InputHTMLAttributes<HTMLInputElement> & { label: string; error?: string; hideLabel?: boolean };

export const Field = forwardRef<HTMLInputElement, Props>(({ label, error, hideLabel, id, className = "", ...props }, ref) => {
  const autoId = useId();
  const fieldId = id ?? autoId;
  return (
    <div className="flex flex-col gap-1">
      <label htmlFor={fieldId} className={hideLabel ? "sr-only" : "text-sm font-medium text-ink"}>
        {label}
      </label>
      <input
        ref={ref}
        id={fieldId}
        aria-invalid={!!error}
        aria-describedby={error ? `${fieldId}-error` : undefined}
        className={`min-h-11 rounded border border-rule bg-panel px-3 py-2 text-ink outline-none focus:border-sea ${
          error ? "border-murram" : ""
        } ${className}`}
        {...props}
      />
      {error && (
        <p id={`${fieldId}-error`} className="text-sm text-murram">
          {error}
        </p>
      )}
    </div>
  );
});
Field.displayName = "Field";
