from rest_framework.permissions import BasePermission

from apps.accounts.models import Role

# Coarse, role-derived capability list surfaced to the client at /api/v1/me/.
# This is UX only (section 7 of IMPLEMENTATION_REACT.md): it lets the client
# hide controls a user cannot use. Every endpoint still enforces its own
# scope/role check server-side; this list is never trusted as the boundary.
PERMISSIONS_BY_ROLE: dict[str, list[str]] = {
    Role.NATIONAL_ADMIN: ["trend.approve", "metrics.national.view", "metrics.district.view", "parish.view", "admin.manage"],
    Role.DISTRICT_OFFICER: ["trend.approve", "metrics.district.view", "parish.view"],
    Role.SUBCOUNTY_OFFICER: ["parish.view", "farmer.register", "lot.manage"],
    Role.PARISH_CHIEF: ["parish.view", "declaration.create", "lot.manage"],
    Role.AGENT: ["farmer.register", "declaration.create"],
    Role.BUYER: ["bid.create"],
    Role.FARMER: ["farmer.home.view"],
}


def permissions_for(user) -> list[str]:
    return PERMISSIONS_BY_ROLE.get(user.role, [])


class IsNationalAdmin(BasePermission):
    """Gate for the admin configuration API (geography, crops, seasons,
    users, buyers) — the only role that manages system-wide reference data."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == Role.NATIONAL_ADMIN)


# Roles with operational authority over a parish/subcounty/district — as
# opposed to farmer/buyer, whose accounts also carry a scope_level/scope_id
# (for their own home parish or national reach) but never authority over
# anyone else's records. parish_ids_for() alone does not distinguish these:
# a farmer's own scope_id resolves the same way an officer's does, so
# anything that hands out officer-only visibility (parish dashboards,
# advisory request queues) needs this role check too.
OFFICER_ROLES = (Role.AGENT, Role.PARISH_CHIEF, Role.SUBCOUNTY_OFFICER, Role.DISTRICT_OFFICER, Role.NATIONAL_ADMIN)


class IsOfficer(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role in OFFICER_ROLES)
