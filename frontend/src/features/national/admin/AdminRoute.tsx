import * as Tabs from "@radix-ui/react-tabs";

import { BuyersPanel } from "./BuyersPanel";
import { CropsPanel } from "./CropsPanel";
import { DistrictsPanel } from "./DistrictsPanel";
import { FarmersPanel } from "./FarmersPanel";
import { ParishesPanel } from "./ParishesPanel";
import { SeasonsPanel } from "./SeasonsPanel";
import { SubcountiesPanel } from "./SubcountiesPanel";
import { UsersPanel } from "./UsersPanel";
import { VillagesPanel } from "./VillagesPanel";

const TABS = [
  { value: "users", label: "Users", Panel: UsersPanel },
  { value: "farmers", label: "Farmers", Panel: FarmersPanel },
  { value: "districts", label: "Districts", Panel: DistrictsPanel },
  { value: "subcounties", label: "Subcounties", Panel: SubcountiesPanel },
  { value: "parishes", label: "Parishes", Panel: ParishesPanel },
  { value: "villages", label: "Villages", Panel: VillagesPanel },
  { value: "crops", label: "Crops", Panel: CropsPanel },
  { value: "seasons", label: "Seasons", Panel: SeasonsPanel },
  { value: "buyers", label: "Buyers", Panel: BuyersPanel },
];

function AdminRoute() {
  return (
    <div className="mx-auto flex max-w-4xl flex-col gap-4 p-4">
      <h1 className="text-lg font-semibold text-ink">Configuration</h1>
      <Tabs.Root defaultValue="users">
        <Tabs.List className="flex flex-wrap gap-1 border-b border-rule">
          {TABS.map((t) => (
            <Tabs.Trigger
              key={t.value}
              value={t.value}
              className="rounded-t px-3 py-2 text-sm text-soft outline-none data-[state=active]:border-b-2 data-[state=active]:border-sea data-[state=active]:font-medium data-[state=active]:text-ink"
            >
              {t.label}
            </Tabs.Trigger>
          ))}
        </Tabs.List>
        {TABS.map((t) => (
          <Tabs.Content key={t.value} value={t.value} className="pt-4">
            <t.Panel />
          </Tabs.Content>
        ))}
      </Tabs.Root>
    </div>
  );
}

export default AdminRoute;
