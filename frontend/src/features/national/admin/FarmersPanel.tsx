import { type FormEvent, useState } from "react";

import type { components } from "../../../api/schema";
import { Button } from "../../../design/ui/Button";
import { Field } from "../../../design/ui/Field";
import { ResourceTable } from "../../../design/ui/ResourceTable";
import { Select } from "../../../design/ui/Select";
import { useAdminResource } from "./useAdminResource";

type Village = components["schemas"]["VillageAdmin"];
type Farmer = components["schemas"]["FarmerAdmin"];

const EMPTY = { full_name: "", sex: "F" as "F" | "M", phone: "", villageId: "" };

export function FarmersPanel() {
  const villages = useAdminResource<Village>("villages");
  const { list, create, update, remove } = useAdminResource<Farmer>("farmers");
  const [editingId, setEditingId] = useState<number | null>(null);
  const [draft, setDraft] = useState(EMPTY);

  function startCreate() {
    setEditingId(0);
    setDraft({ ...EMPTY, villageId: villages.list.data?.[0]?.id ? String(villages.list.data[0].id) : "" });
  }
  function startEdit(row: Farmer) {
    setEditingId(row.id);
    setDraft({ full_name: row.full_name, sex: row.sex, phone: row.phone ?? "", villageId: String(row.village) });
  }
  function cancel() {
    setEditingId(null);
  }
  function onSubmit(e: FormEvent) {
    e.preventDefault();
    const body = {
      full_name: draft.full_name, sex: draft.sex,
      phone: draft.phone || null, village: Number(draft.villageId),
    };
    if (editingId) update.mutate({ id: editingId, ...body }, { onSuccess: cancel });
    else create.mutate(body, { onSuccess: cancel });
  }

  return (
    <div className="flex flex-col gap-4">
      <p className="text-sm text-soft">
        Plot and planting details aren't managed here — farmers set those up through registration
        (agent or self sign-up). This is for the core profile.
      </p>

      {editingId !== null ? (
        <form onSubmit={onSubmit} className="flex flex-wrap items-end gap-3 rounded-lg bg-panel p-4">
          <Field label="Full name" required value={draft.full_name}
            onChange={(e) => setDraft({ ...draft, full_name: e.target.value })} />
          <Select label="Sex" value={draft.sex} onChange={(e) => setDraft({ ...draft, sex: e.target.value as "F" | "M" })}>
            <option value="F">Female</option>
            <option value="M">Male</option>
          </Select>
          <Field label="Phone (optional)" value={draft.phone} onChange={(e) => setDraft({ ...draft, phone: e.target.value })} />
          <Select label="Village" required value={draft.villageId} onChange={(e) => setDraft({ ...draft, villageId: e.target.value })}>
            {villages.list.data?.map((v) => (
              <option key={v.id} value={v.id}>
                {v.name} ({v.parish_name})
              </option>
            ))}
          </Select>
          <Button type="submit" disabled={create.isPending || update.isPending}>
            {editingId ? "Save" : "Add"}
          </Button>
          <Button type="button" variant="ghost" onClick={cancel}>
            Cancel
          </Button>
        </form>
      ) : (
        <Button onClick={startCreate} className="self-start">
          Add farmer
        </Button>
      )}

      {list.data && (
        <ResourceTable
          columns={[
            { key: "full_name", label: "Name" },
            { key: "village_name", label: "Village" },
            { key: "parish_name", label: "Parish" },
            { key: "phone", label: "Phone" },
            { key: "registered_by_name", label: "Registered by", render: (r) => r.registered_by_name ?? "self" },
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
