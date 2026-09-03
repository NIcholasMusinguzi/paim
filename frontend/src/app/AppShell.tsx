import { Outlet } from "react-router";

import { AppHeader } from "./AppHeader";

export function AppShell() {
  return (
    <div className="min-h-screen bg-page text-ink">
      <AppHeader />
      <Outlet />
    </div>
  );
}
