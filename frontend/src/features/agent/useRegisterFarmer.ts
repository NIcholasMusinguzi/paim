import { useMutation, useQueryClient } from "@tanstack/react-query";

import { db, type QueuedOp } from "./db";
import { syncNow } from "./sync";

export interface FarmerInput {
  full_name: string;
  village_id: number;
  village_name: string;
  sex: string;
  phone?: string;
}

// Writes go to the outbox first and to the local mirror optimistically, so
// the agent sees their own work immediately whether or not there is a
// network (IMPLEMENTATION_REACT.md section 8).
export function useRegisterFarmer() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (input: FarmerInput) => {
      const op_id = crypto.randomUUID();
      const op: QueuedOp = {
        op_id,
        type: "farmer.create",
        payload: {
          full_name: input.full_name,
          village_id: input.village_id,
          sex: input.sex,
          ...(input.phone ? { phone: input.phone } : {}),
        },
        at: new Date().toISOString(),
        status: "queued",
        attempts: 0,
      };
      await db.outbox.add(op);
      await db.farmers.add({
        id: -Date.now(),
        op_id,
        full_name: input.full_name,
        village_id: input.village_id,
        village_name: input.village_name,
        sex: input.sex,
        phone: input.phone,
        pending: true,
      });
      void syncNow();
      return op;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["agent", "farmers"] }),
  });
}
