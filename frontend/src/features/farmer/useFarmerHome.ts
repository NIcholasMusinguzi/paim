import { useQuery } from "@tanstack/react-query";

import { api } from "../../api/client";
import type { components } from "../../api/schema";

export type FarmerHome = components["schemas"]["FarmerHome"];

export function useFarmerHome() {
  return useQuery({
    queryKey: ["farmer", "home"] as const,
    queryFn: () => api<FarmerHome>("/farmer/home/"),
  });
}
