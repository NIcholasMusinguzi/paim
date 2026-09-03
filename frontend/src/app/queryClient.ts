import { QueryClient } from "@tanstack/react-query";

import { ApiError } from "../api/client";

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      gcTime: 10 * 60_000,
      retry: (count, err) => !(err instanceof ApiError && err.status < 500) && count < 2,
      refetchOnWindowFocus: false, // costs data on a metered connection
      networkMode: "offlineFirst",
    },
    mutations: { networkMode: "offlineFirst" },
  },
});

export const qk = {
  me: ["me"] as const,
  parishDashboard: (id: number) => ["parish", id, "dashboard"] as const,
  parishes: ["parishes"] as const,
};
