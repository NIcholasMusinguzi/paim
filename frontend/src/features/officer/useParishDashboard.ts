import { useQuery } from "@tanstack/react-query";

import { api } from "../../api/client";
import type { components } from "../../api/schema";
import { qk } from "../../app/queryClient";

export type ParishDashboard = components["schemas"]["ParishDashboard"];
export type ParishListItem = components["schemas"]["ParishList"];

export function useParishDashboard(parishId: number | null) {
  return useQuery({
    queryKey: parishId != null ? qk.parishDashboard(parishId) : ["parish", "none"],
    queryFn: () => api<ParishDashboard>(`/parish/${parishId}/dashboard/`),
    enabled: parishId != null,
  });
}

export function useParishes() {
  return useQuery({
    queryKey: qk.parishes,
    queryFn: () => api<ParishListItem[]>("/parishes/"),
  });
}
