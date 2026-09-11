import { useQuery } from "@tanstack/react-query";

import { api } from "../../api/client";
import { useAuth } from "../../app/AuthProvider";
import { Card } from "../../design/ui/Card";
import { EmptyState } from "../../design/ui/EmptyState";
import { FarmersPanel } from "../national/admin/FarmersPanel";

type FarmerRow = {
  id: number;
  full_name: string;
  sex: string;
  phone: string | null;
  village: string;
  parish: string;
  subcounty: string;
  district: string;
  crops: string[];
};

function FarmerDirectory() {
  const list = useQuery({
    queryKey: ["farmers"] as const,
    queryFn: () => api<FarmerRow[]>("/farmers/"),
  });
  const rows = list.data;

  return (
    <Card title="Farmers in your area">
      {!rows || rows.length === 0 ? (
        <EmptyState title="No farmers registered in your area yet." />
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-rule text-xs text-soft">
                <th className="py-2 pr-3">Name</th>
                <th className="py-2 pr-3">Crops</th>
                <th className="py-2 pr-3">Village</th>
                <th className="py-2 pr-3">Parish</th>
                <th className="py-2 pr-3">Subcounty</th>
                <th className="py-2 pr-3">District</th>
                <th className="py-2 pr-3">Phone</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.id} className="border-b border-rule last:border-0">
                  <td className="py-2.5 pr-3 text-ink">{row.full_name}</td>
                  <td className="py-2.5 pr-3 text-ink">{row.crops?.length ? row.crops.join(", ") : "—"}</td>
                  <td className="py-2.5 pr-3 text-ink">{row.village}</td>
                  <td className="py-2.5 pr-3 text-ink">{row.parish}</td>
                  <td className="py-2.5 pr-3 text-ink">{row.subcounty}</td>
                  <td className="py-2.5 pr-3 text-ink">{row.district}</td>
                  <td className="py-2.5 pr-3 text-ink">{row.phone || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Card>
  );
}

function FarmersRoute() {
  const { me } = useAuth();
  return (
    <div className="mx-auto flex max-w-5xl flex-col gap-4">
      {me?.role === "national_admin" ? <FarmersPanel /> : <FarmerDirectory />}
    </div>
  );
}

export const Component = FarmersRoute;
