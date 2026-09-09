import * as Tabs from "@radix-ui/react-tabs";

import { Card } from "../../../design/ui/Card";

import { BuyersPanel } from "./BuyersPanel";
import { MarketPricesPanel } from "./MarketPricesPanel";
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
  { value: "prices", label: "Market prices", Panel: MarketPricesPanel },
];

function AdminRoute() {
  return (
    <Card title="Configuration">
      <Tabs.Root defaultValue="users">
        <Tabs.List className="mb-2 flex flex-wrap gap-1 border-b border-rule">
          {TABS.map((t) => (
            <Tabs.Trigger
              key={t.value}
              value={t.value}
              className="rounded-t px-3 py-2 text-sm text-soft outline-none data-[state=active]:border-b-2 data-[state=active]:border-leaf data-[state=active]:font-medium data-[state=active]:text-ink"
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
    </Card>
  );
}

export default AdminRoute;
