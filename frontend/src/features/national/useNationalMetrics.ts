import { useQueries, useQuery } from "@tanstack/react-query";

import { api } from "../../api/client";
import type { components } from "../../api/schema";

export type ReferenceData = components["schemas"]["ReferenceData"];
export type NationalMetricsResponse = components["schemas"]["NationalMetricsResponse"];
export type DistrictMetric = components["schemas"]["DistrictMetric"];
export type ParishMetric = {
  id: number;
  parish_id: number;
  parish: string;
  farmers_registered: number;
  farmers_active: number;
  bags_declared: number;
  pct_grade1: number;
  avg_price_per_kg: number | null;
  agent_reach: number;
  live: boolean;
};

export type SeasonBar = {
  season_id: number;
  label: string;
  pct_grade1: number;
  avg_price_per_kg: number | null;
};

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

export function useCropNationalMetrics(
  seasonId: number | null,
  crops: { id: number; name: string }[] | undefined,
) {
  return useQueries({
    queries: (crops ?? []).map((crop) => ({
      queryKey: ["metrics", "national", seasonId, crop.id] as const,
      queryFn: () => api<NationalMetricsResponse>(`/metrics/national/?season=${seasonId}&crop=${crop.id}`),
      enabled: seasonId != null,
    })),
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

export function useDistrictSeasonBars(districtId: number | null, cropId: number | null) {
  return useQuery({
    queryKey: ["metrics", "district-seasons", districtId, cropId] as const,
    queryFn: () => api<SeasonBar[]>(`/metrics/district/${districtId}/seasons/?crop=${cropId}`),
    enabled: districtId != null && cropId != null,
  });
}
