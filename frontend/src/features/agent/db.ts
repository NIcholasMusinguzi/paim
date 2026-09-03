import Dexie, { type Table } from "dexie";

export type OpType = "farmer.create" | "declaration.create" | "declaration.grade";
export type OpStatus = "queued" | "applied" | "rejected" | "needs_attention";

export interface QueuedOp {
  op_id: string;
  type: OpType;
  payload: Record<string, unknown>;
  at: string;
  status: OpStatus;
  attempts: number;
  reason?: string;
}

export interface CachedFarmer {
  id: number; // negative = local-only, not yet confirmed by the server
  op_id?: string; // the op that created it, to reconcile once synced
  full_name: string;
  village_id: number;
  village_name: string;
  sex?: string;
  phone?: string;
  pending: boolean;
  needs_attention?: boolean;
  reason?: string;
}

export interface CachedVillage {
  id: number;
  name: string;
}

export interface CachedCrop {
  id: number;
  name: string;
}

export interface CachedLot {
  id: number;
  crop_id: number;
  crop: string;
  bags: number;
  min_bags: number;
}

export const db = new Dexie("paim-agent") as Dexie & {
  outbox: Table<QueuedOp, string>;
  farmers: Table<CachedFarmer, number>;
  villages: Table<CachedVillage, number>;
  crops: Table<CachedCrop, number>;
  lots: Table<CachedLot, number>;
};

db.version(1).stores({
  outbox: "op_id, status, at",
  farmers: "id, op_id, village_id, full_name",
  villages: "id, name",
  crops: "id, name",
  lots: "id, crop_id",
});
