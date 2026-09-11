import { Link, useLocation } from "react-router";

import { Icons } from "../design/ui/Icon";
import { isNavActive, navForRole } from "./nav";
import { useAuth } from "./AuthProvider";

export function AppSidebar({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const { me } = useAuth();
  const location = useLocation();
  if (!me) return null;
  const links = navForRole(me.role);

  return (
    <>
      <div
        className={`fixed inset-0 z-40 bg-ink/40 transition-opacity lg:hidden ${open ? "opacity-100" : "pointer-events-none opacity-0"}`}
        onClick={onClose}
        aria-hidden={!open}
      />
      <aside
        className={`fixed inset-y-0 left-0 z-50 flex w-64 flex-col bg-sea text-white transition-transform lg:translate-x-0 ${
          open ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="flex shrink-0 items-center gap-2 px-5 py-5">
          <Icons.logo className="h-9 w-9" />
          <div>
            <p className="text-lg font-bold tracking-tight">PAIM</p>
            <p className="text-[10px] uppercase tracking-wider text-sprout">
              Agri-tech
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="ml-auto rounded-lg p-2 text-sprout lg:hidden"
            aria-label="Close menu"
          >
            <Icons.close />
          </button>
        </div>

        <nav className="min-h-0 flex-1 overflow-y-auto px-3 [scrollbar-color:rgba(143,209,158,0.55)_transparent] [scrollbar-width:thin]">
          {links.map((link) => {
            const Icon = Icons[link.icon];
            const active = isNavActive(link, location.pathname, location.hash);
            return (
              <Link
                key={`${link.label}-${link.to}`}
                to={link.to}
                onClick={onClose}
                className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${
                  active
                    ? "bg-white/15 text-white"
                    : "text-sprout hover:bg-white/10 hover:text-white"
                }`}
              >
                <span
                  className={`h-5 w-0.5 rounded-full ${active ? "bg-leaf" : "bg-transparent"}`}
                />
                <Icon className="h-4 w-4" />
                {link.label}
              </Link>
            );
          })}
        </nav>

        <div className="mt-auto shrink-0 overflow-hidden px-4 pb-5">
          <div className="relative overflow-hidden rounded-xl bg-white/10 p-4">
            <svg
              viewBox="0 0 160 80"
              className="absolute inset-0 h-full w-full opacity-40"
              aria-hidden
            >
              <ellipse cx="80" cy="70" rx="80" ry="16" fill="#1b5e38" />
              <path
                d="M0 50c20-10 40 4 60-2 20-6 30-16 50-12 20 4 30 8 50 2v42H0z"
                fill="#2f9e44"
              />
            </svg>
            <p className="relative text-xs leading-relaxed font-medium text-white">
              Better information. Stronger farmers. Greater markets.
            </p>
          </div>
        </div>
      </aside>
    </>
  );
}
