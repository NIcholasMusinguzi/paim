import { type FormEvent, useState } from "react";

import { Button } from "../../../design/ui/Button";
import { Field } from "../../../design/ui/Field";
import { ResourceTable } from "../../../design/ui/ResourceTable";
import { Select } from "../../../design/ui/Select";
import { useAdminResource } from "./useAdminResource";

type Category = "produce" | "input";
type Price = {
  id: number;
  item_name: string;
  category: Category;
  price: number;
  unit: string;
  market: string;
  price_date: string;
  source: string;
};
type Draft = Omit<Price, "id" | "price"> & { price: string };
const EMPTY: Draft = {
  item_name: "",
  category: "produce",
  price: "",
  unit: "kg",
  market: "",
  price_date: new Date().toISOString().slice(0, 10),
  source: "",
};

export function MarketPricesPanel() {
  const { list, create, update, remove } =
    useAdminResource<Price>("market-prices");
  const [editingId, setEditingId] = useState<number | null>(null);
  const [draft, setDraft] = useState<Draft>(EMPTY);
  function submit(event: FormEvent) {
    event.preventDefault();
    const body: Omit<Price, "id"> = { ...draft, price: Number(draft.price) };
    const done = () => setEditingId(null);
    if (editingId)
      update.mutate({ id: editingId, ...body }, { onSuccess: done });
    else create.mutate(body, { onSuccess: done });
  }
  return (
    <div className="flex flex-col gap-4">
      {editingId !== null ? (
        <form
          onSubmit={submit}
          className="flex flex-wrap items-end gap-3 rounded-lg bg-panel p-4"
        >
          <Field
            label="Crop or input"
            required
            value={draft.item_name}
            onChange={(e) => setDraft({ ...draft, item_name: e.target.value })}
          />
          <Select
            label="Type"
            value={draft.category}
            onChange={(e) =>
              setDraft({ ...draft, category: e.target.value as Category })
            }
          >
            <option value="produce">Crop</option>
            <option value="input">Farm input</option>
          </Select>
          <Field
            label="Price"
            type="number"
            min={1}
            required
            value={draft.price}
            onChange={(e) => setDraft({ ...draft, price: e.target.value })}
          />
          <Field
            label="Unit"
            required
            value={draft.unit}
            onChange={(e) => setDraft({ ...draft, unit: e.target.value })}
          />
          <Field
            label="Date"
            type="date"
            required
            value={draft.price_date}
            onChange={(e) => setDraft({ ...draft, price_date: e.target.value })}
          />
          <Field
            label="Market"
            value={draft.market}
            onChange={(e) => setDraft({ ...draft, market: e.target.value })}
          />
          <Button type="submit" disabled={create.isPending || update.isPending}>
            {editingId ? "Save" : "Add price"}
          </Button>
          <Button
            type="button"
            variant="ghost"
            onClick={() => setEditingId(null)}
          >
            Cancel
          </Button>
        </form>
      ) : (
        <Button
          onClick={() => {
            setDraft(EMPTY);
            setEditingId(0);
          }}
          className="self-start"
        >
          Add market price
        </Button>
      )}
      {list.data && (
        <ResourceTable
          columns={[
            { key: "price_date", label: "Date" },
            { key: "item_name", label: "Item" },
            { key: "category", label: "Type" },
            {
              key: "price",
              label: "Price",
              render: (row) => `UGX ${row.price}`,
            },
            { key: "unit", label: "Unit" },
            { key: "market", label: "Market" },
          ]}
          rows={list.data}
          onEdit={(row) => {
            setEditingId(row.id);
            setDraft({
              item_name: row.item_name,
              category: row.category,
              price: String(row.price),
              unit: row.unit,
              market: row.market,
              price_date: row.price_date,
              source: row.source,
            });
          }}
          onDelete={(id) => remove.mutate(id)}
          deleting={remove.isPending}
        />
      )}
    </div>
  );
}
