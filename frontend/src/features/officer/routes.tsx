import { Navigate, Route, Routes } from "react-router";

import OfficerDashboard from "./OfficerRoute";

function OfficerRoutes() {
  return (
    <Routes>
      <Route index element={<OfficerDashboard />} />
      <Route path="reports" element={<Navigate to="/reports" replace />} />
    </Routes>
  );
}

export const Component = OfficerRoutes;
