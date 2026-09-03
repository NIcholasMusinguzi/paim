import { Link, useLocation } from "react-router";

import { useLogout } from "../api/hooks/useMe";
import { Button } from "../design/ui/Button";
import { useAuth } from "./AuthProvider";

// A national admin (or district officer) has access to every parish
// dashboard plus the national view and the insight queue, but nothing
// pointed them at that — this is the fix for "as admin I should see
// everything": the access already existed, it just wasn't discoverable.
const NAV_BY_ROLE: Record<string, { label: string; to: string }[]> = {
  national_admin: [
    { label: "National dashboard", to: "/national" },
    { label: "Insight queue", to: "/national/trends" },
    { label: "Parish dashboard", to: "/parish" },
    { label: "Configuration", to: "/national/admin" },
  ],
  district_officer: [
    { label: "National dashboard", to: "/national" },
    { label: "Insight queue", to: "/national/trends" },
    { label: "Parish dashboard", to: "/parish" },
  ],
  parish_chief: [{ label: "Parish dashboard", to: "/parish" }],
  subcounty_officer: [{ label: "Parish dashboard", to: "/parish" }],
};

export function AppHeader() {
  const { me } = useAuth();
  const logout = useLogout();
  const location = useLocation();

  if (!me) return null;
  const links = NAV_BY_ROLE[me.role];
  if (!links) return null; // farmer/agent/buyer routes are single-page and carry their own header

  return (
    <header className="flex items-center justify-between border-b border-rule bg-panel px-4 py-3">
      <nav className="flex items-center gap-4">
        <span className="font-semibold text-ink">PAIM</span>
        {links.map((link) => (
          <Link
            key={link.to}
            to={link.to}
            className={
              location.pathname === link.to
                ? "text-sm font-medium text-sea"
                : "text-sm text-soft hover:text-ink"
            }
          >
            {link.label}
          </Link>
        ))}
      </nav>
      <div className="flex items-center gap-3">
        <span className="text-xs text-soft">{me.full_name}</span>
        <Button variant="ghost" onClick={() => logout.mutate()} disabled={logout.isPending} className="px-2 py-1 text-sm">
          Sign out
        </Button>
      </div>
    </header>
  );
}
