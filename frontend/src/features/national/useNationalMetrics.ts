import { useQuery } from "@tanstack/react-query";

import { api } from "../../api/client";
import type { components } from "../../api/schema";

export type ReferenceData = components["schemas"]["ReferenceData"];
export type NationalMetricsResponse = components["schemas"]["NationalMetricsResponse"];
export type DistrictMetric = components["schemas"]["DistrictMetric"];
export type ParishMetric = components["schemas"]["ParishMetric"];

export function useReferenceData() {
  return useQuery({
    queryKey: ["reference"] as const,
    queryFn: () => api<ReferenceData>("/reference/"),
    staleTime: 10 * 60_000, // seasons and crops change rarely
  });
}

export function useNationalMetrics(seasonId: number | null, cropId: number | null) {
  return useQuery({
    queryKey: ["metrics", "national", seasonId, cropId] as const,
    queryFn: () => api<NationalMetricsResponse>(`/metrics/national/?season=${seasonId}&crop=${cropId}`),
    enabled: seasonId != null && cropId != null,
  });
}

export function useDistrictParishes(districtId: number | null, seasonId: number | null, cropId: number | null) {
  return useQuery({
    queryKey: ["metrics", "district", districtId, seasonId, cropId] as const,
    queryFn: () =>
      api<ParishMetric[]>(`/metrics/district/${districtId}/parishes/?season=${seasonId}&crop=${cropId}`),
    enabled: districtId != null && seasonId != null && cropId != null,
  });
}
