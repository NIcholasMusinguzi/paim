import { type FormEvent, useState } from "react";

import type { components } from "../../../api/schema";
import { Button } from "../../../design/ui/Button";
import { Field } from "../../../design/ui/Field";
import { ResourceTable } from "../../../design/ui/ResourceTable";
import { Select } from "../../../design/ui/Select";
import { useAdminResource } from "./useAdminResource";

type Parish = components["schemas"]["ParishAdmin"];
type Village = components["schemas"]["VillageAdmin"];

export function VillagesPanel() {
  const parishes = useAdminResource<Parish>("parishes");
  const { list, create, update, remove } = useAdminResource<Village>("villages");
  const [editingId, setEditingId] = useState<number | null>(null);
  const [name, setName] = useState("");
  const [parishId, setParishId] = useState("");

  function startCreate() {
    setEditingId(0);
    setName("");
    setParishId(parishes.list.data?.[0]?.id ? String(parishes.list.data[0].id) : "");
  }
  function startEdit(row: Village) {
    setEditingId(row.id);
    setName(row.name);
    setParishId(String(row.parish));
  }
  function cancel() {
    setEditingId(null);
  }
  function onSubmit(e: FormEvent) {
    e.preventDefault();
    const body = { name, parish: Number(parishId) };
    if (editingId) update.mutate({ id: editingId, ...body }, { onSuccess: cancel });
    else create.mutate(body, { onSuccess: cancel });
  }

  return (
    <div className="flex flex-col gap-4">
      {editingId !== null ? (
        <form onSubmit={onSubmit} className="flex flex-wrap items-end gap-3 rounded-lg bg-panel p-4">
          <Field label="Name" required value={name} onChange={(e) => setName(e.target.value)} />
          <Select label="Parish" required value={parishId} onChange={(e) => setParishId(e.target.value)}>
            {parishes.list.data?.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name} ({p.district_name})
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
          Add village
        </Button>
      )}

      {list.data && (
        <ResourceTable
          columns={[
            { key: "name", label: "Name" },
            { key: "parish_name", label: "Parish" },
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
