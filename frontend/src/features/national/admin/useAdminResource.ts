import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "../../../api/client";

// Generic CRUD over the admin configuration API (geography, crops,
// seasons, users, buyers). All of it is plain reference-data CRUD with no
// domain rules of its own — the rules live in the serializers server-side
// (scope validation, role checks); this hook is just wiring.
export function useAdminResource<T extends { id: number }>(resource: string) {
  const qc = useQueryClient();
  const key = ["admin", resource] as const;
  const base = `/admin/${resource}/`;

  const list = useQuery({ queryKey: key, queryFn: () => api<T[]>(base) });

  const create = useMutation({
    mutationFn: (body: Partial<T>) => api<T>(base, { method: "POST", body: JSON.stringify(body) }),
    onSuccess: () => qc.invalidateQueries({ queryKey: key }),
  });

  const update = useMutation({
    mutationFn: ({ id, ...body }: Partial<T> & { id: number }) =>
      api<T>(`${base}${id}/`, { method: "PATCH", body: JSON.stringify(body) }),
    onSuccess: () => qc.invalidateQueries({ queryKey: key }),
  });

  const remove = useMutation({
    mutationFn: (id: number) => api<void>(`${base}${id}/`, { method: "DELETE" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: key }),
  });

  return { list, create, update, remove };
}
