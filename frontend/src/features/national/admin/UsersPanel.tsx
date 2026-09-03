import { type FormEvent, useState } from "react";

import { ApiError } from "../../../api/client";
import type { components } from "../../../api/schema";
import { Button } from "../../../design/ui/Button";
import { Field } from "../../../design/ui/Field";
import { Pill } from "../../../design/ui/Pill";
import { ResourceTable } from "../../../design/ui/ResourceTable";
import { Select } from "../../../design/ui/Select";
import { useAdminResource } from "./useAdminResource";

type SystemUser = components["schemas"]["SystemUserAdmin"];
type District = components["schemas"]["DistrictAdmin"];
type Subcounty = components["schemas"]["SubcountyAdmin"];
type Parish = components["schemas"]["ParishAdmin"];

const ROLES = ["national_admin", "district_officer", "subcounty_officer", "parish_chief", "agent", "buyer", "farmer"] as const;

const EMPTY = { phone: "", full_name: "", password: "", role: "agent" as string, scopeLevel: "parish" as string, scopeId: "" };

function scopeLevelFor(role: string): string {
  if (role === "national_admin" || role === "buyer") return "national";
  if (role === "district_officer") return "district";
  if (role === "subcounty_officer") return "subcounty";
  return "parish"; // parish_chief, agent, farmer
}

export function UsersPanel() {
  const districts = useAdminResource<District>("districts");
  const subcounties = useAdminResource<Subcounty>("subcounties");
  const parishes = useAdminResource<Parish>("parishes");
  const { list, create, update } = useAdminResource<SystemUser>("users");
  const [editingId, setEditingId] = useState<number | null>(null);
  const [draft, setDraft] = useState(EMPTY);

  function startCreate() {
    setEditingId(0);
    setDraft(EMPTY);
  }
  function startEdit(row: SystemUser) {
    setEditingId(row.id);
    setDraft({
      phone: row.phone, full_name: row.full_name, password: "",
      role: row.role, scopeLevel: row.scope_level, scopeId: row.scope_id != null ? String(row.scope_id) : "",
    });
  }
  function cancel() {
    setEditingId(null);
  }
  function onRoleChange(role: string) {
    setDraft({ ...draft, role, scopeLevel: scopeLevelFor(role), scopeId: "" });
  }

  const [error, setError] = useState<string | null>(null);

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    const scopeless = draft.scopeLevel === "national";
    const body: Partial<SystemUser> = {
      phone: draft.phone, full_name: draft.full_name,
      role: draft.role as SystemUser["role"], scope_level: draft.scopeLevel as SystemUser["scope_level"],
      scope_id: scopeless ? null : Number(draft.scopeId),
      ...(draft.password ? { password: draft.password } : {}),
    };
    const onError = (err: unknown) => setError(err instanceof ApiError ? err.detail : "Something went wrong.");
    if (editingId) update.mutate({ id: editingId, ...body }, { onSuccess: cancel, onError });
    else create.mutate(body, { onSuccess: cancel, onError });
  }

  function toggleActive(row: SystemUser) {
    update.mutate({ id: row.id, is_active: !row.is_active });
  }

  return (
    <div className="flex flex-col gap-4">
      {editingId !== null ? (
        <form onSubmit={onSubmit} className="flex flex-col gap-3 rounded-lg bg-panel p-4">
          <div className="flex flex-wrap items-end gap-3">
            <Field label="Full name" required value={draft.full_name} onChange={(e) => setDraft({ ...draft, full_name: e.target.value })} />
            <Field label="Phone" required value={draft.phone} onChange={(e) => setDraft({ ...draft, phone: e.target.value })} />
            <Field label={editingId ? "New password (leave blank to keep)" : "Password"} type="password"
              minLength={6} required={!editingId} value={draft.password}
              onChange={(e) => setDraft({ ...draft, password: e.target.value })} />
          </div>
          <div className="flex flex-wrap items-end gap-3">
            <Select label="Role" value={draft.role} onChange={(e) => onRoleChange(e.target.value)}>
              {ROLES.map((r) => (
                <option key={r} value={r}>
                  {r.replace("_", " ")}
                </option>
              ))}
            </Select>
            {draft.scopeLevel === "district" && (
              <Select label="District" required value={draft.scopeId} onChange={(e) => setDraft({ ...draft, scopeId: e.target.value })}>
                <option value="">Select…</option>
                {districts.list.data?.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
              </Select>
            )}
            {draft.scopeLevel === "subcounty" && (
              <Select label="Subcounty" required value={draft.scopeId} onChange={(e) => setDraft({ ...draft, scopeId: e.target.value })}>
                <option value="">Select…</option>
                {subcounties.list.data?.map((s) => <option key={s.id} value={s.id}>{s.name} ({s.district_name})</option>)}
              </Select>
            )}
            {draft.scopeLevel === "parish" && (
              <Select label="Parish" required value={draft.scopeId} onChange={(e) => setDraft({ ...draft, scopeId: e.target.value })}>
                <option value="">Select…</option>
                {parishes.list.data?.map((p) => <option key={p.id} value={p.id}>{p.name} ({p.district_name})</option>)}
              </Select>
            )}
            {draft.scopeLevel === "national" && <p className="pb-2 text-sm text-soft">National scope — no location needed.</p>}
          </div>
          {error && <p role="alert" className="text-sm text-murram">{error}</p>}
          <div className="flex gap-2">
            <Button type="submit" disabled={create.isPending || update.isPending}>
              {editingId ? "Save" : "Add"}
            </Button>
            <Button type="button" variant="ghost" onClick={cancel}>
              Cancel
            </Button>
          </div>
        </form>
      ) : (
        <Button onClick={startCreate} className="self-start">
          Add user
        </Button>
      )}

      {list.data && (
        <ResourceTable
          columns={[
            { key: "full_name", label: "Name" },
            { key: "phone", label: "Phone" },
            { key: "role", label: "Role", render: (r) => r.role.replace("_", " ") },
            { key: "scope_level", label: "Scope" },
            {
              key: "is_active", label: "Status",
              render: (r) => (
                <button onClick={() => toggleActive(r)}>
                  <Pill tone={r.is_active ? "leaf" : "murram"}>{r.is_active ? "active" : "deactivated"}</Pill>
                </button>
              ),
            },
          ]}
          rows={list.data}
          onEdit={startEdit}
        />
      )}
    </div>
  );
}
