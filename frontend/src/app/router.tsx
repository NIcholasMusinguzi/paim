import { createBrowserRouter } from "react-router";

import { AppShell } from "./AppShell";
import { RequireRole, RoleRedirect } from "./RequireRole";
import { RootError } from "./RootError";

export const router = createBrowserRouter([
  { path: "/sign-in", lazy: () => import("../features/auth/SignInRoute") },
  { path: "/sign-up", lazy: () => import("../features/auth/SignUpRoute") },
  {
    element: <AppShell />,
    errorElement: <RootError />,
    children: [
      { index: true, element: <RoleRedirect /> },
      {
        element: <RequireRole roles={["farmer"]} />,
        children: [{ path: "farmer/*", lazy: () => import("../features/farmer/routes") }],
      },
      {
        element: <RequireRole roles={["agent"]} />,
        children: [{ path: "agent/*", lazy: () => import("../features/agent/routes") }],
      },
      {
        element: <RequireRole roles={["parish_chief", "subcounty_officer", "district_officer", "national_admin"]} />,
        children: [{ path: "parish/*", lazy: () => import("../features/officer/routes") }],
      },
      {
        element: <RequireRole roles={["district_officer", "national_admin"]} />,
        children: [{ path: "national/*", lazy: () => import("../features/national/routes") }],
      },
      {
        element: <RequireRole roles={["buyer"]} />,
        children: [{ path: "buyer/*", lazy: () => import("../features/buyer/routes") }],
      },
    ],
  },
]);
