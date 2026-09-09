import { describe, expect, it } from "vitest";

import { isNavActive, type NavItem } from "./nav";

describe("isNavActive", () => {
  const dashboard: NavItem = { label: "Dashboard", to: "/national", icon: "grid", match: "exact" };
  const admin: NavItem = { label: "Farmers", to: "/national/admin", icon: "users", match: "prefix" };
  const weather: NavItem = { label: "Weather", to: "/national#weather", icon: "cloud", match: "exact" };

  it("highlights the national dashboard only on the exact path", () => {
    expect(isNavActive(dashboard, "/national")).toBe(true);
    expect(isNavActive(dashboard, "/national/admin")).toBe(false);
  });

  it("highlights prefix routes under configuration", () => {
    expect(isNavActive(admin, "/national/admin")).toBe(true);
    expect(isNavActive(admin, "/national")).toBe(false);
  });

  it("highlights hash links when the hash matches", () => {
    expect(isNavActive(weather, "/national", "#weather")).toBe(true);
    expect(isNavActive(weather, "/national", "")).toBe(false);
  });
});
