import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "../../api/client";
import type { components } from "../../api/schema";

export type TrendInsight = components["schemas"]["TrendInsight"] & { scope_name?: string };

export function useTrends(status: "pending" | "published") {
  return useQuery({
    queryKey: ["trends", status] as const,
    queryFn: () => api<TrendInsight[]>(`/trends/?status=${status}`),
  });
}

export function useApproveTrend() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (insightId: number) => api<TrendInsight>(`/trends/${insightId}/approve/`, { method: "POST" }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["trends", "pending"] });
      qc.invalidateQueries({ queryKey: ["trends", "published"] });
    },
  });
}
