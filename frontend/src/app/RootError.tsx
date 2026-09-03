import { useRouteError } from "react-router";

import { EmptyState } from "../design/ui/EmptyState";

export function RootError() {
  useRouteError();
  return (
    <div className="flex min-h-screen items-center justify-center bg-page p-6">
      <EmptyState title="Something went wrong loading PAIM. Reload the page to try again." />
    </div>
  );
}
