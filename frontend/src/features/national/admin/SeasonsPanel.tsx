import { type FormEvent, useState } from "react";

import type { components } from "../../../api/schema";
import { Button } from "../../../design/ui/Button";
import { Field } from "../../../design/ui/Field";
import { ResourceTable } from "../../../design/ui/ResourceTable";
import { Select } from "../../../design/ui/Select";
import { useAdminResource } from "./useAdminResource";

type Season = components["schemas"]["SeasonAdmin"];

const SEASON_LABEL: Record<number, string> = { 1: "A", 2: "B" };

const EMPTY = { year: String(new Date().getFullYear()), season_no: "1", start_date: "", end_date: "" };

export function SeasonsPanel() {
  const { list, create, update, remove } = useAdminResource<Season>("seasons");
  const [editingId, setEditingId] = useState<number | null>(null);
  const [draft, setDraft] = useState(EMPTY);

  function startCreate() {
    setEditingId(0);
    setDraft(EMPTY);
  }
  function startEdit(row: Season) {
    setEditingId(row.id);
    setDraft({
      year: String(row.year), season_no: String(row.season_no),
      start_date: row.start_date, end_date: row.end_date,
    });
  }
  function cancel() {
    setEditingId(null);
  }
  function onSubmit(e: FormEvent) {
    e.preventDefault();
    const body = {
      year: Number(draft.year), season_no: Number(draft.season_no) as 1 | 2,
      start_date: draft.start_date, end_date: draft.end_date,
    };
    if (editingId) update.mutate({ id: editingId, ...body }, { onSuccess: cancel });
    else create.mutate(body, { onSuccess: cancel });
  }

  return (
    <div className="flex flex-col gap-4">
      {editingId !== null ? (
        <form onSubmit={onSubmit} className="flex flex-wrap items-end gap-3 rounded-lg bg-panel p-4">
          <Field label="Year" type="number" required value={draft.year}
            onChange={(e) => setDraft({ ...draft, year: e.target.value })} className="w-24" />
          <Select label="Season" value={draft.season_no} onChange={(e) => setDraft({ ...draft, season_no: e.target.value })}>
            <option value="1">A</option>
            <option value="2">B</option>
          </Select>
          <Field label="Start date" type="date" required value={draft.start_date}
            onChange={(e) => setDraft({ ...draft, start_date: e.target.value })} />
          <Field label="End date" type="date" required value={draft.end_date}
            onChange={(e) => setDraft({ ...draft, end_date: e.target.value })} />
          <Button type="submit" disabled={create.isPending || update.isPending}>
            {editingId ? "Save" : "Add"}
          </Button>
          <Button type="button" variant="ghost" onClick={cancel}>
            Cancel
          </Button>
        </form>
      ) : (
        <Button onClick={startCreate} className="self-start">
          Add season
        </Button>
      )}

      {list.data && (
        <ResourceTable
          columns={[
            { key: "year", label: "Year" },
            { key: "season_no", label: "Season", render: (r) => SEASON_LABEL[r.season_no] ?? r.season_no },
            { key: "start_date", label: "Start" },
            { key: "end_date", label: "End" },
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
