import { humanStatus } from "./humanStatus";

const BASE = import.meta.env.VITE_API_BASE ?? "/api/v1";

export class ApiError extends Error {
  status: number;
  detail: string;
  fields?: Record<string, string[]>;

  constructor(status: number, detail: string, fields?: Record<string, string[]>) {
    super(detail);
    this.status = status;
    this.detail = detail;
    this.fields = fields;
  }
}

function csrf(): string {
  return document.cookie.match(/csrftoken=([^;]+)/)?.[1] ?? "";
}

let refreshing: Promise<void> | null = null;

export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const run = () =>
    fetch(`${BASE}${path}`, {
      ...init,
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
        ...(init.method && init.method !== "GET" ? { "X-CSRFToken": csrf() } : {}),
        ...init.headers,
      },
    });

  let res = await run();

  if (res.status === 401 && !path.startsWith("/auth/")) {
    refreshing ??= fetch(`${BASE}/auth/refresh/`, {
      method: "POST",
      credentials: "include",
      headers: { "X-CSRFToken": csrf() },
    })
      .then((r) => {
        if (!r.ok) throw new ApiError(401, humanStatus(401));
      })
      .finally(() => {
        refreshing = null;
      });
    await refreshing;
    res = await run(); // one retry, never a loop
  }

  if (!res.ok) {
    const body = await res.json().catch(() => ({}) as { detail?: string; errors?: Record<string, string[]> });
    throw new ApiError(res.status, body.detail ?? humanStatus(res.status), body.errors);
  }
  return res.status === 204 ? (undefined as T) : res.json();
}
