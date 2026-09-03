from apps.accounts.models import Role, ScopeLevel
from apps.geo.models import Parish


def parish_ids_for(user):
    if user.role == Role.NATIONAL_ADMIN:
        return Parish.objects.values_list("id", flat=True)
    if user.scope_level == ScopeLevel.DISTRICT:
        return Parish.objects.filter(subcounty__district_id=user.scope_id).values_list("id", flat=True)
    if user.scope_level == ScopeLevel.SUBCOUNTY:
        return Parish.objects.filter(subcounty_id=user.scope_id).values_list("id", flat=True)
    if user.scope_level == ScopeLevel.PARISH:
        return Parish.objects.filter(id=user.scope_id).values_list("id", flat=True)
    return Parish.objects.none()


class ScopedQuerysetMixin:
    parish_path = "parish_id"

    def get_queryset(self):
        return super().get_queryset().filter(**{f"{self.parish_path}__in": parish_ids_for(self.request.user)})
