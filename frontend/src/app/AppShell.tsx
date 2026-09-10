import { useState } from "react";
import { Outlet } from "react-router";

import { useAuth } from "./AuthProvider";
import { AppSidebar } from "./AppSidebar";
import { AppTopbar } from "./AppTopbar";

export function AppShell() {
  const { me } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);

  if (!me) {
    return (
      <div className="min-h-screen bg-page text-ink">
        <Outlet />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-page text-ink">
      <AppSidebar open={menuOpen} onClose={() => setMenuOpen(false)} />
      <div className="lg:pl-64">
        <AppTopbar onMenu={() => setMenuOpen(true)} />
        <main className="p-4 md:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
