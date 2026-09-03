import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "../../api/client";
import type { components } from "../../api/schema";

export type BuyerLot = components["schemas"]["BuyerLot"];
export type LotDetail = components["schemas"]["LotDetail"];
type BidInput = components["schemas"]["BidInput"];

export function useOpenLots() {
  return useQuery({
    queryKey: ["buyer", "lots"] as const,
    queryFn: () => api<BuyerLot[]>("/buyer/lots/"),
  });
}

export function useLotDetail(lotId: number | null) {
  return useQuery({
    queryKey: ["lot", lotId] as const,
    queryFn: () => api<LotDetail>(`/lots/${lotId}/`),
    enabled: lotId != null,
  });
}

export function useSubmitBid(lotId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: BidInput) =>
      api<LotDetail>(`/lots/${lotId}/bids/`, { method: "POST", body: JSON.stringify(body) }),
    onSuccess: (lot) => qc.setQueryData(["lot", lotId], lot),
  });
}
