import { Route, Routes } from "react-router";

import { RequireRole } from "../../app/RequireRole";
import AdminRoute from "./admin/AdminRoute";
import NationalDashboard from "./NationalRoute";
import TrendsRoute from "./TrendsRoute";
import { FarmersPanel } from "./admin/FarmersPanel";
import ReportsRoute from "../officer/ReportsRoute";

function NationalRoutes() {
  return (
    <Routes>
      <Route index element={<NationalDashboard />} />
      <Route path="trends" element={<TrendsRoute />} />
      <Route path="reports" element={<ReportsRoute />} />
      <Route path="farmers" element={<FarmersPanel />} />
      <Route element={<RequireRole roles={["national_admin"]} />}>
        <Route path="admin" element={<AdminRoute />} />
      </Route>
    </Routes>
  );
}

export const Component = NationalRoutes;
