import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "../client";
import type { components } from "../schema";

export type AdvisoryRequest = components["schemas"]["AdvisoryRequest"];

export function useMyAdvisoryRequests() {
  return useQuery({
    queryKey: ["advisoryRequests", "mine"] as const,
    queryFn: () => api<AdvisoryRequest[]>("/advisory-requests/mine/"),
  });
}

export function useSubmitAdvisoryRequest() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (message: string) =>
      api<AdvisoryRequest>("/advisory-requests/mine/", { method: "POST", body: JSON.stringify({ message }) }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["advisoryRequests", "mine"] }),
  });
}

export function useAdvisoryQueue() {
  return useQuery({
    queryKey: ["advisoryRequests", "queue"] as const,
    queryFn: () => api<AdvisoryRequest[]>("/advisory-requests/queue/"),
  });
}

export function useRespondToRequest() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, body }: { id: number; body: string }) =>
      api<AdvisoryRequest>(`/advisory-requests/${id}/respond/`, { method: "POST", body: JSON.stringify({ body }) }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["advisoryRequests", "queue"] }),
  });
}
