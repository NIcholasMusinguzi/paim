import { useQuery } from "@tanstack/react-query";

import { api } from "../client";

export type MarketPrice = {
  id: number;
  item_name: string;
  category: "produce" | "input";
  price: number;
  unit: string;
  market: string;
  price_date: string;
  source: string;
};

export function useMarketPrices() {
  return useQuery({
    queryKey: ["market-prices", "daily"] as const,
    queryFn: () => api<MarketPrice[]>("/market-prices/daily/"),
  });
}
