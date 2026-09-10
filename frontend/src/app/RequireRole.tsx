import { Navigate, Outlet } from "react-router";

import { useAuth } from "./AuthProvider";

// A convenience, not a control: every endpoint enforces scope server-side
// through parish_ids_for(). Hiding a route here is UX, never the security
// boundary (IMPLEMENTATION_REACT.md section 7).
export function RequireAuth() {
  const { me, isLoading } = useAuth();
  if (isLoading) return null;
  if (!me) return <Navigate to="/sign-in" replace />;
  return <Outlet />;
}

export function RequireRole({ roles }: { roles: string[] }) {
  const { me, isLoading } = useAuth();
  if (isLoading) return null;
  if (!me) return <Navigate to="/sign-in" replace />;
  if (!roles.includes(me.role)) return <Navigate to="/" replace />;
  return <Outlet />;
}

const HOME_BY_ROLE: Record<string, string> = {
  farmer: "/farmer",
  agent: "/agent",
  parish_chief: "/parish",
  subcounty_officer: "/parish",
  district_officer: "/national",
  national_admin: "/national",
  buyer: "/buyer",
};

export function RoleRedirect() {
  const { me, isLoading } = useAuth();
  if (isLoading) return null;
  if (!me) return <Navigate to="/sign-in" replace />;
  return <Navigate to={HOME_BY_ROLE[me.role] ?? "/sign-in"} replace />;
}
