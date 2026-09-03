import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { qk } from "../../app/queryClient";
import { api } from "../client";
import type { components } from "../schema";

export type Me = components["schemas"]["Me"];
type LoginBody = components["schemas"]["Login"];
type SignupBody = components["schemas"]["Signup"];
export type VillageOption = components["schemas"]["VillageList"];

export function useMe() {
  return useQuery({
    queryKey: qk.me,
    queryFn: () => api<Me>("/me/"),
    retry: false,
  });
}

export function useLogin() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: LoginBody) => api<Me>("/auth/login/", { method: "POST", body: JSON.stringify(body) }),
    onSuccess: (me) => qc.setQueryData(qk.me, me),
  });
}

export function useSignup() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: SignupBody) => api<Me>("/auth/signup/", { method: "POST", body: JSON.stringify(body) }),
    onSuccess: (me) => qc.setQueryData(qk.me, me),
  });
}

export function useVillages() {
  return useQuery({
    queryKey: ["villages"] as const,
    queryFn: () => api<VillageOption[]>("/villages/"),
    staleTime: 10 * 60_000,
  });
}

export function useLogout() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => api<void>("/auth/logout/", { method: "POST" }),
    onSuccess: () => qc.setQueryData(qk.me, null),
  });
}
