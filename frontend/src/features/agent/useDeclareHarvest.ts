import { useMutation, useQueryClient } from "@tanstack/react-query";

import { db, type QueuedOp } from "./db";
import { syncNow } from "./sync";

export interface DeclarationInput {
  farmer_id: number;
  crop_id: number;
  bags: number;
}

export function useDeclareHarvest() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (input: DeclarationInput) => {
      const op_id = crypto.randomUUID();
      const op: QueuedOp = {
        op_id,
        type: "declaration.create",
        payload: { farmer_id: input.farmer_id, crop_id: input.crop_id, bags: input.bags },
        at: new Date().toISOString(),
        status: "queued",
        attempts: 0,
      };
      await db.outbox.add(op);
      void syncNow();
      return op;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["agent", "lots"] }),
  });
}
