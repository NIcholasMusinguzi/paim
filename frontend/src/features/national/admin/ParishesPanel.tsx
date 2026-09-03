import { type FormEvent, useState } from "react";

import type { components } from "../../../api/schema";
import { Button } from "../../../design/ui/Button";
import { Field } from "../../../design/ui/Field";
import { ResourceTable } from "../../../design/ui/ResourceTable";
import { Select } from "../../../design/ui/Select";
import { useAdminResource } from "./useAdminResource";

type Subcounty = components["schemas"]["SubcountyAdmin"];
type Parish = components["schemas"]["ParishAdmin"];

const EMPTY = { name: "", subcountyId: "", agro_zone: "Lake Victoria Crescent", lot_min_bags: "800" };

export function ParishesPanel() {
  const subcounties = useAdminResource<Subcounty>("subcounties");
  const { list, create, update, remove } = useAdminResource<Parish>("parishes");
  const [editingId, setEditingId] = useState<number | null>(null);
  const [draft, setDraft] = useState(EMPTY);

  function startCreate() {
    setEditingId(0);
    setDraft({ ...EMPTY, subcountyId: subcounties.list.data?.[0]?.id ? String(subcounties.list.data[0].id) : "" });
  }
  function startEdit(row: Parish) {
    setEditingId(row.id);
    setDraft({
      name: row.name, subcountyId: String(row.subcounty),
      agro_zone: row.agro_zone ?? "Lake Victoria Crescent", lot_min_bags: String(row.lot_min_bags ?? 800),
    });
  }
  function cancel() {
    setEditingId(null);
  }
  function onSubmit(e: FormEvent) {
    e.preventDefault();
    const body = {
      name: draft.name, subcounty: Number(draft.subcountyId),
      agro_zone: draft.agro_zone, lot_min_bags: Number(draft.lot_min_bags),
    };
    if (editingId) update.mutate({ id: editingId, ...body }, { onSuccess: cancel });
    else create.mutate(body, { onSuccess: cancel });
  }

  return (
    <div className="flex flex-col gap-4">
      {editingId !== null ? (
        <form onSubmit={onSubmit} className="flex flex-wrap items-end gap-3 rounded-lg bg-panel p-4">
          <Field label="Name" required value={draft.name} onChange={(e) => setDraft({ ...draft, name: e.target.value })} />
          <Select label="Subcounty" required value={draft.subcountyId}
            onChange={(e) => setDraft({ ...draft, subcountyId: e.target.value })}>
            {subcounties.list.data?.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name} ({s.district_name})
              </option>
            ))}
          </Select>
          <Field label="Agro zone" value={draft.agro_zone} onChange={(e) => setDraft({ ...draft, agro_zone: e.target.value })} />
          <Field label="Lot minimum (bags)" type="number" min={1} value={draft.lot_min_bags}
            onChange={(e) => setDraft({ ...draft, lot_min_bags: e.target.value })} className="w-32" />
          <Button type="submit" disabled={create.isPending || update.isPending}>
            {editingId ? "Save" : "Add"}
          </Button>
          <Button type="button" variant="ghost" onClick={cancel}>
            Cancel
          </Button>
        </form>
      ) : (
        <Button onClick={startCreate} className="self-start">
          Add parish
        </Button>
      )}

      {list.data && (
        <ResourceTable
          columns={[
            { key: "name", label: "Name" },
            { key: "subcounty_name", label: "Subcounty" },
            { key: "district_name", label: "District" },
            { key: "lot_min_bags", label: "Lot min (bags)" },
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
