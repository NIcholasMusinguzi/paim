import { type FormEvent, useState } from "react";

import type { components } from "../../../api/schema";
import { Button } from "../../../design/ui/Button";
import { Field } from "../../../design/ui/Field";
import { ResourceTable } from "../../../design/ui/ResourceTable";
import { Select } from "../../../design/ui/Select";
import { useAdminResource } from "./useAdminResource";

type SystemUser = components["schemas"]["SystemUserAdmin"];
type Buyer = components["schemas"]["BuyerAdmin"];

const EMPTY = { name: "", licence_no: "", userId: "" };

export function BuyersPanel() {
  const users = useAdminResource<SystemUser>("users");
  const { list, create, update, remove } = useAdminResource<Buyer>("buyers");
  const [editingId, setEditingId] = useState<number | null>(null);
  const [draft, setDraft] = useState(EMPTY);

  const buyerUsers = (users.list.data ?? []).filter((u) => u.role === "buyer");

  function startCreate() {
    setEditingId(0);
    setDraft({ ...EMPTY, userId: buyerUsers[0] ? String(buyerUsers[0].id) : "" });
  }
  function startEdit(row: Buyer) {
    setEditingId(row.id);
    setDraft({ name: row.name, licence_no: row.licence_no, userId: String(row.user) });
  }
  function cancel() {
    setEditingId(null);
  }
  function onSubmit(e: FormEvent) {
    e.preventDefault();
    const body = { name: draft.name, licence_no: draft.licence_no, user: Number(draft.userId) };
    if (editingId) update.mutate({ id: editingId, ...body }, { onSuccess: cancel });
    else create.mutate(body, { onSuccess: cancel });
  }

  return (
    <div className="flex flex-col gap-4">
      {editingId !== null ? (
        <form onSubmit={onSubmit} className="flex flex-wrap items-end gap-3 rounded-lg bg-panel p-4">
          <Field label="Company name" required value={draft.name}
            onChange={(e) => setDraft({ ...draft, name: e.target.value })} />
          <Field label="Licence no." required value={draft.licence_no}
            onChange={(e) => setDraft({ ...draft, licence_no: e.target.value })} />
          <Select label="Login account" required value={draft.userId}
            onChange={(e) => setDraft({ ...draft, userId: e.target.value })}>
            {buyerUsers.length === 0 && <option value="">No buyer-role accounts yet — create one under Users</option>}
            {buyerUsers.map((u) => (
              <option key={u.id} value={u.id}>
                {u.full_name} ({u.phone})
              </option>
            ))}
          </Select>
          <Button type="submit" disabled={create.isPending || update.isPending || buyerUsers.length === 0}>
            {editingId ? "Save" : "Add"}
          </Button>
          <Button type="button" variant="ghost" onClick={cancel}>
            Cancel
          </Button>
        </form>
      ) : (
        <Button onClick={startCreate} className="self-start">
          Add buyer
        </Button>
      )}

      {list.data && (
        <ResourceTable
          columns={[
            { key: "name", label: "Company" },
            { key: "licence_no", label: "Licence" },
            { key: "user_phone", label: "Login phone" },
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
