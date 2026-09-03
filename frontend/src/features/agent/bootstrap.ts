import { api } from "../../api/client";
import type { components } from "../../api/schema";
import { db } from "./db";

type Bootstrap = components["schemas"]["Bootstrap"];

// Cache on bootstrap: parish roster, crop reference data, and the open
// lot(s), so the agent can register and declare with no signal
// (IMPLEMENTATION.md section 9).
export async function bootstrap(): Promise<void> {
  const data = await api<Bootstrap>("/sync/bootstrap/");
  const villageName = new Map(data.villages.map((v) => [v.id, v.name] as const));

  await db.transaction("rw", db.villages, db.crops, db.lots, db.farmers, async () => {
    await db.villages.bulkPut(data.villages);
    await db.crops.bulkPut(data.crops);
    await db.lots.clear();
    await db.lots.bulkPut(data.open_lots);

    for (const f of data.farmers) {
      const existing = await db.farmers.get(f.id);
      await db.farmers.put({
        id: f.id,
        full_name: f.full_name,
        village_id: f.village_id,
        village_name: villageName.get(f.village_id) ?? "",
        sex: existing?.sex,
        phone: f.phone ?? undefined,
        pending: false,
      });
    }
  });
}
