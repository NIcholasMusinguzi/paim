export const ROLE_LABEL: Record<string, string> = {
  national_admin: "National Admin",
  district_officer: "District Officer",
  subcounty_officer: "Subcounty Officer",
  parish_chief: "Parish Officer",
  agent: "Village Agent",
  farmer: "Farmer",
  buyer: "Buyer",
};

export type NavItem = {
  label: string;
  to: string;
  icon: "grid" | "users" | "megaphone" | "cloud" | "chart" | "truck" | "file" | "gear" | "home";
  match?: "exact" | "prefix";
};

const OFFICER_NAV: NavItem[] = [
  { label: "Dashboard", to: "/national", icon: "grid", match: "exact" },
  { label: "Farmers", to: "/national/farmers", icon: "users", match: "prefix" },
  { label: "Advisories", to: "/parish", icon: "megaphone", match: "prefix" },
  { label: "Weather", to: "/national#weather", icon: "cloud", match: "exact" },
  { label: "Market Prices", to: "/national#prices", icon: "chart", match: "exact" },
  { label: "Bulk Sales", to: "/parish", icon: "truck", match: "prefix" },
  { label: "Reports", to: "/national/reports", icon: "file", match: "prefix" },
  { label: "Settings", to: "/national/admin", icon: "gear", match: "prefix" },
];

const PARISH_NAV: NavItem[] = [
  { label: "Dashboard", to: "/parish", icon: "grid", match: "prefix" },
  { label: "Advisories", to: "/parish#advisories", icon: "megaphone", match: "prefix" },
  { label: "Weather", to: "/parish#weather", icon: "cloud", match: "prefix" },
  { label: "Market Prices", to: "/parish#prices", icon: "chart", match: "prefix" },
  { label: "Bulk Sales", to: "/parish#sales", icon: "truck", match: "prefix" },
  { label: "Reports", to: "/parish/reports", icon: "file", match: "prefix" },
];

const FARMER_NAV: NavItem[] = [{ label: "Home", to: "/farmer", icon: "home", match: "prefix" }];
const AGENT_NAV: NavItem[] = [{ label: "Farmers", to: "/agent", icon: "users", match: "prefix" }];
const BUYER_NAV: NavItem[] = [{ label: "Open lots", to: "/buyer", icon: "truck", match: "prefix" }];

export function navForRole(role: string): NavItem[] {
  if (role === "national_admin" || role === "district_officer") return OFFICER_NAV.filter((item) => {
    if (role === "district_officer" && (item.label === "Farmers" || item.label === "Settings")) return false;
    return true;
  });
  if (role === "parish_chief" || role === "subcounty_officer") return PARISH_NAV;
  if (role === "farmer") return FARMER_NAV;
  if (role === "agent") return AGENT_NAV;
  if (role === "buyer") return BUYER_NAV;
  return [];
}

export function locationLabel(role: string, scopeLevel: string): string {
  if (scopeLevel === "national") return "Uganda";
  if (role === "farmer") return "My farm";
  if (scopeLevel === "district") return "District view";
  if (scopeLevel === "subcounty") return "Subcounty view";
  if (scopeLevel === "parish") return "Parish view";
  return "PAIM";
}

export function isNavActive(item: NavItem, pathname: string, hash = ""): boolean {
  const [path, itemHash] = item.to.split("#");
  const onPath = pathname === path || pathname === `${path}/` || (item.match === "prefix" && pathname.startsWith(`${path}/`));
  if (!onPath) return false;
  if (itemHash) return hash === `#${itemHash}`;
  if (item.match === "exact") return pathname === path || pathname === `${path}/`;
  return onPath;
}
