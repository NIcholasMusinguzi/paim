import { useLogout, useUpdateMe } from "../api/hooks/useMe";
import { useState } from "react";
import { ApiError } from "../api/client";
import { Button } from "../design/ui/Button";
import { Field } from "../design/ui/Field";
import { formatLongDate, initials } from "../design/format";
import { Icons } from "../design/ui/Icon";
import { useAuth } from "./AuthProvider";
import { ROLE_LABEL, locationLabel } from "./nav";

export function AppTopbar({ onMenu }: { onMenu: () => void }) {
  const { me } = useAuth();
  const logout = useLogout();
  const updateMe = useUpdateMe();
  const [profileOpen, setProfileOpen] = useState(false);
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState({
    full_name: me?.full_name ?? "",
    phone: me?.phone ?? "",
  });
  if (!me) return null;

  return (
    <header className="sticky top-0 z-30 flex items-center gap-3 border-b border-rule bg-panel px-4 py-3">
      <button
        type="button"
        onClick={onMenu}
        className="rounded-lg p-2 text-sea lg:hidden"
        aria-label="Open menu"
      >
        <Icons.menu />
      </button>

      <div className="flex items-center gap-2 rounded-lg border border-rule bg-page px-3 py-1.5 text-sm text-ink">
        <Icons.home className="h-4 w-4 text-leaf" />
        <span className="font-medium">
          {locationLabel(me.role, me.scope.level)}
        </span>
      </div>

      <p className="hidden text-sm text-soft md:block">{formatLongDate()}</p>

      <div className="ml-auto flex items-center gap-3">
        <span
          className="relative rounded-lg p-2 text-soft"
          aria-label="Notifications"
        >
          <Icons.bell className="h-5 w-5" />
        </span>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => {
              setDraft({ full_name: me.full_name, phone: me.phone });
              setProfileOpen(true);
            }}
            className="flex h-9 w-9 items-center justify-center rounded-full bg-sea text-xs font-semibold text-white"
            aria-label="Open profile"
          >
            {initials(me.full_name)}
          </button>
          <div className="hidden leading-tight sm:block">
            <p className="text-sm font-semibold text-ink">{me.full_name}</p>
            <p className="text-xs text-soft">
              {ROLE_LABEL[me.role] ?? me.role}
            </p>
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
      {profileOpen && (
        <div
          className="fixed inset-0 z-50 flex items-start justify-center bg-ink/40 p-4 pt-20"
          onClick={() => setProfileOpen(false)}
        >
          <section
            className="w-full max-w-md rounded-xl bg-panel p-5 shadow-xl"
            onClick={(event) => event.stopPropagation()}
            role="dialog"
            aria-modal="true"
            aria-labelledby="profile-title"
          >
            <div className="flex items-center justify-between">
              <h2 id="profile-title" className="text-lg font-semibold text-ink">
                My profile
              </h2>
              <button
                type="button"
                onClick={() => setProfileOpen(false)}
                className="text-soft"
                aria-label="Close profile"
              >
                ×
              </button>
            </div>
            {editing ? (
              <form
                className="mt-4 flex flex-col gap-3"
                onSubmit={(event) => {
                  event.preventDefault();
                  updateMe.mutate(draft, {
                    onSuccess: () => setEditing(false),
                  });
                }}
              >
                <Field
                  label="Full name"
                  value={draft.full_name}
                  onChange={(event) =>
                    setDraft({ ...draft, full_name: event.target.value })
                  }
                />
                <Field
                  label="Phone"
                  value={draft.phone}
                  onChange={(event) =>
                    setDraft({ ...draft, phone: event.target.value })
                  }
                />
                {updateMe.isError && (
                  <p className="text-sm text-murram">
                    {updateMe.error instanceof ApiError
                      ? updateMe.error.detail
                      : "Could not update profile."}
                  </p>
                )}
                <div className="flex gap-2">
                  <Button type="submit" disabled={updateMe.isPending}>
                    Save changes
                  </Button>
                  <Button
                    type="button"
                    variant="ghost"
                    onClick={() => setEditing(false)}
                  >
                    Cancel
                  </Button>
                </div>
              </form>
            ) : (
              <div className="mt-4 flex flex-col gap-3 text-sm">
                <p className="text-ink">
                  <strong>Name:</strong> {me.full_name}
                </p>
                <p className="text-ink">
                  <strong>Phone:</strong> {me.phone}
                </p>
                <p className="text-ink">
                  <strong>Role:</strong> {ROLE_LABEL[me.role] ?? me.role}
                </p>
                <p className="text-ink">
                  <strong>Scope:</strong>{" "}
                  {locationLabel(me.role, me.scope.level)}
                </p>
                <Button onClick={() => setEditing(true)} className="self-start">
                  Edit profile
                </Button>
              </div>
            )}
          </section>
        </div>
      )}
    </header>
  );
}
