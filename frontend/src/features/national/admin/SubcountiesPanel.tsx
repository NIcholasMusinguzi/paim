import { type FormEvent, useState } from "react";

import type { components } from "../../../api/schema";
import { Button } from "../../../design/ui/Button";
import { Field } from "../../../design/ui/Field";
import { ResourceTable } from "../../../design/ui/ResourceTable";
import { Select } from "../../../design/ui/Select";
import { useAdminResource } from "./useAdminResource";

type District = components["schemas"]["DistrictAdmin"];
type Subcounty = components["schemas"]["SubcountyAdmin"];

export function SubcountiesPanel() {
  const districts = useAdminResource<District>("districts");
  const { list, create, update, remove } = useAdminResource<Subcounty>("subcounties");
  const [editingId, setEditingId] = useState<number | null>(null);
  const [name, setName] = useState("");
  const [districtId, setDistrictId] = useState("");

  function startCreate() {
    setEditingId(0);
    setName("");
    setDistrictId(districts.list.data?.[0]?.id ? String(districts.list.data[0].id) : "");
  }
  function startEdit(row: Subcounty) {
    setEditingId(row.id);
    setName(row.name);
    setDistrictId(String(row.district));
  }
  function cancel() {
    setEditingId(null);
  }
  function onSubmit(e: FormEvent) {
    e.preventDefault();
    const body = { name, district: Number(districtId) };
    if (editingId) update.mutate({ id: editingId, ...body }, { onSuccess: cancel });
    else create.mutate(body, { onSuccess: cancel });
  }

  return (
    <div className="flex flex-col gap-4">
      {editingId !== null ? (
        <form onSubmit={onSubmit} className="flex flex-wrap items-end gap-3 rounded-lg bg-panel p-4">
          <Field label="Name" required value={name} onChange={(e) => setName(e.target.value)} />
          <Select label="District" required value={districtId} onChange={(e) => setDistrictId(e.target.value)}>
            {districts.list.data?.map((d) => (
              <option key={d.id} value={d.id}>
                {d.name}
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
          Add subcounty
        </Button>
      )}

      {list.data && (
        <ResourceTable
          columns={[
            { key: "name", label: "Name" },
            { key: "district_name", label: "District" },
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
