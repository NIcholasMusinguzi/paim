import { Navigate, Route, Routes } from "react-router";

import { RequireRole } from "../../app/RequireRole";
import AdminRoute from "./admin/AdminRoute";
import NationalDashboard from "./NationalRoute";
import TrendsRoute from "./TrendsRoute";

function NationalRoutes() {
  return (
    <Routes>
      <Route index element={<NationalDashboard />} />
      <Route path="trends" element={<TrendsRoute />} />
      <Route path="reports" element={<Navigate to="/reports" replace />} />
      <Route path="farmers" element={<Navigate to="/farmers" replace />} />
      <Route element={<RequireRole roles={["national_admin"]} />}>
        <Route path="admin" element={<AdminRoute />} />
      </Route>
    </Routes>
  );
}

export const Component = NationalRoutes;
