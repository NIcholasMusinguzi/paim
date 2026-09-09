import { useLogout } from "../api/hooks/useMe";
import { formatLongDate, initials } from "../design/format";
import { Icons } from "../design/ui/Icon";
import { useAuth } from "./AuthProvider";
import { ROLE_LABEL, locationLabel } from "./nav";

export function AppTopbar({ onMenu }: { onMenu: () => void }) {
  const { me } = useAuth();
  const logout = useLogout();
  if (!me) return null;

  return (
    <header className="sticky top-0 z-30 flex items-center gap-3 border-b border-rule bg-panel px-4 py-3">
      <button type="button" onClick={onMenu} className="rounded-lg p-2 text-sea lg:hidden" aria-label="Open menu">
        <Icons.menu />
      </button>

      <div className="flex items-center gap-2 rounded-lg border border-rule bg-page px-3 py-1.5 text-sm text-ink">
        <Icons.home className="h-4 w-4 text-leaf" />
        <span className="font-medium">{locationLabel(me.role, me.scope.level)}</span>
      </div>

      <p className="hidden text-sm text-soft md:block">{formatLongDate()}</p>

      <div className="ml-auto flex items-center gap-3">
        <span className="relative rounded-lg p-2 text-soft" aria-label="Notifications">
          <Icons.bell className="h-5 w-5" />
        </span>
        <div className="flex items-center gap-2">
          <span className="flex h-9 w-9 items-center justify-center rounded-full bg-sea text-xs font-semibold text-white">
            {initials(me.full_name)}
          </span>
          <div className="hidden leading-tight sm:block">
            <p className="text-sm font-semibold text-ink">{me.full_name}</p>
            <p className="text-xs text-soft">{ROLE_LABEL[me.role] ?? me.role}</p>
          </div>
        </div>
        <button
          type="button"
          onClick={() => logout.mutate()}
          disabled={logout.isPending}
          className="rounded-lg p-2 text-soft hover:bg-page hover:text-sea"
          aria-label="Sign out"
        >
          <Icons.logout className="h-5 w-5" />
        </button>
      </div>
    </header>
  );
}
