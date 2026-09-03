import { type FormEvent, useState } from "react";

import type { components } from "../../../api/schema";
import { Button } from "../../../design/ui/Button";
import { Field } from "../../../design/ui/Field";
import { ResourceTable } from "../../../design/ui/ResourceTable";
import { useAdminResource } from "./useAdminResource";

type District = components["schemas"]["DistrictAdmin"];

const EMPTY = { name: "", region: "Central" };

export function DistrictsPanel() {
  const { list, create, update, remove } = useAdminResource<District>("districts");
  const [editingId, setEditingId] = useState<number | null>(null);
  const [draft, setDraft] = useState(EMPTY);

  function startCreate() {
    setEditingId(0);
    setDraft(EMPTY);
  }
  function startEdit(row: District) {
    setEditingId(row.id);
    setDraft({ name: row.name, region: row.region ?? "Central" });
  }
  function cancel() {
    setEditingId(null);
    setDraft(EMPTY);
  }
  function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (editingId) {
      update.mutate({ id: editingId, ...draft }, { onSuccess: cancel });
    } else {
      create.mutate(draft, { onSuccess: cancel });
    }
  }

  return (
    <div className="flex flex-col gap-4">
      {editingId !== null ? (
        <form onSubmit={onSubmit} className="flex flex-wrap items-end gap-3 rounded-lg bg-panel p-4">
          <Field label="Name" required value={draft.name} onChange={(e) => setDraft({ ...draft, name: e.target.value })} />
          <Field label="Region" required value={draft.region} onChange={(e) => setDraft({ ...draft, region: e.target.value })} />
          <Button type="submit" disabled={create.isPending || update.isPending}>
            {editingId ? "Save" : "Add"}
          </Button>
          <Button type="button" variant="ghost" onClick={cancel}>
            Cancel
          </Button>
        </form>
      ) : (
        <Button onClick={startCreate} className="self-start">
          Add district
        </Button>
      )}

      {list.data && (
        <ResourceTable
          columns={[
            { key: "name", label: "Name" },
            { key: "region", label: "Region" },
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
