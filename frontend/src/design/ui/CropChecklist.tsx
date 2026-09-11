type Crop = { id: number; name: string };

export function CropChecklist({
  crops,
  selected,
  onChange,
}: {
  crops: Crop[];
  selected: number[];
  onChange: (ids: number[]) => void;
}) {
  return (
    <fieldset className="flex min-w-[12rem] flex-col gap-1">
      <legend className="text-sm font-medium text-ink">Crops grown</legend>
      <div className="flex flex-wrap gap-2">
        {crops.map((crop) => {
          const checked = selected.includes(crop.id);
          return (
            <label
              key={crop.id}
              className={`inline-flex cursor-pointer items-center gap-2 rounded-lg border px-3 py-2 text-sm ${
                checked ? "border-leaf bg-leaf/10 text-ink" : "border-rule bg-panel text-ink"
              }`}
            >
              <input
                type="checkbox"
                className="accent-leaf"
                checked={checked}
                onChange={(e) =>
                  onChange(
                    e.target.checked
                      ? [...selected, crop.id]
                      : selected.filter((id) => id !== crop.id),
                  )
                }
              />
              {crop.name}
            </label>
          );
        })}
      </div>
    </fieldset>
  );
}
