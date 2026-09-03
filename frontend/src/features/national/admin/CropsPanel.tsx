import { type FormEvent, useState } from "react";

import type { components } from "../../../api/schema";
import { Button } from "../../../design/ui/Button";
import { Field } from "../../../design/ui/Field";
import { ResourceTable } from "../../../design/ui/ResourceTable";
import { useAdminResource } from "./useAdminResource";

type Crop = components["schemas"]["CropAdmin"];

export function CropsPanel() {
  const { list, create, update, remove } = useAdminResource<Crop>("crops");
  const [editingId, setEditingId] = useState<number | null>(null);
  const [name, setName] = useState("");
  const [cycleWeeks, setCycleWeeks] = useState("14");

  function startCreate() {
    setEditingId(0);
    setName("");
    setCycleWeeks("14");
  }
  function startEdit(row: Crop) {
    setEditingId(row.id);
    setName(row.name);
    setCycleWeeks(String(row.cycle_weeks ?? 14));
  }
  function cancel() {
    setEditingId(null);
  }
  function onSubmit(e: FormEvent) {
    e.preventDefault();
    const body = { name, cycle_weeks: Number(cycleWeeks) };
    if (editingId) update.mutate({ id: editingId, ...body }, { onSuccess: cancel });
    else create.mutate(body, { onSuccess: cancel });
  }

  return (
    <div className="flex flex-col gap-4">
      {editingId !== null ? (
        <form onSubmit={onSubmit} className="flex flex-wrap items-end gap-3 rounded-lg bg-panel p-4">
          <Field label="Name" required value={name} onChange={(e) => setName(e.target.value)} />
          <Field label="Cycle (weeks)" type="number" min={1} required value={cycleWeeks}
            onChange={(e) => setCycleWeeks(e.target.value)} className="w-28" />
          <Button type="submit" disabled={create.isPending || update.isPending}>
            {editingId ? "Save" : "Add"}
          </Button>
          <Button type="button" variant="ghost" onClick={cancel}>
            Cancel
          </Button>
        </form>
      ) : (
        <Button onClick={startCreate} className="self-start">
          Add crop
        </Button>
      )}

      {list.data && (
        <ResourceTable
          columns={[
            { key: "name", label: "Name" },
            { key: "cycle_weeks", label: "Cycle (weeks)" },
          ]}
          rows={list.data}
          onEdit={startEdit}
          onDelete={(id) => remove.mutate(id)}
          deleting={remove.isPending}
        />
      )}
    </div>
  );
}
