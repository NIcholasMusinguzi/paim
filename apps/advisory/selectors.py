
from django.db.models import Q
from django.utils import timezone

from apps.accounts.models import Role, ScopeLevel
from apps.accounts.permissions import OFFICER_ROLES
from apps.advisory.models import AdvisoryContent, AdvisoryRequest, Post
from apps.farmers.models import Planting, Season


def crop_week(planting, on=None):
    on = on or timezone.localdate()
    return max(0, (on - planting.planting_date).days // 7)


def current_season(on=None):
    on = on or timezone.localdate()
    return Season.objects.filter(start_date__lte=on, end_date__gte=on).order_by("-year", "-season_no").first()


def advice_for(farmer, on=None):
    season = current_season(on)
    if not season:
        return []
    zone = farmer.village.parish.agro_zone
    output = []
    plantings = Planting.objects.filter(
        plot__farmer=farmer, season=season).select_related("crop")
    for planting in plantings:
        week = crop_week(planting, on)
        qs = AdvisoryContent.objects.filter(crop=planting.crop, status="validated", language=farmer.language,
                                            week_from__lte=week, week_to__gte=week).filter(Q(agro_zone=zone) | Q(agro_zone="")).order_by("-agro_zone")
        if not qs.exists():
            qs = AdvisoryContent.objects.filter(
                crop=planting.crop, status="validated", language="en", week_from__lte=week, week_to__gte=week)
        output.extend(qs[:2])
    return output


def posts_visible_to(user):
    """Same shape as farmer_home()'s trend visibility: national + the
    user's own district + the user's own parish, derived from
    parish_ids_for() so it can never diverge from the one scoping rule."""
    from apps.accounts.scoping import parish_ids_for
    from apps.geo.models import Parish

    if user.role == Role.NATIONAL_ADMIN:
        return Post.objects.select_related("author").order_by("-created_at")

    parish_ids = list(parish_ids_for(user))
    district_ids = list(
        Parish.objects.filter(id__in=parish_ids).values_list("subcounty__district_id", flat=True).distinct())
    return Post.objects.filter(
        Q(scope_level=ScopeLevel.NATIONAL)
        | Q(scope_level=ScopeLevel.DISTRICT, scope_id__in=district_ids)
        | Q(scope_level=ScopeLevel.PARISH, scope_id__in=parish_ids)
    ).select_related("author").order_by("-created_at")


def advisory_requests_visible_to(user):
    """The "shared parish queue": visible to anyone with operational
    authority over the farmer's parish, not a bespoke assignment — and
    restricted to officer-tier roles, since parish_ids_for() alone would
    also match the farmer's own account."""
    if user.role not in OFFICER_ROLES:
        return AdvisoryRequest.objects.none()
    from apps.accounts.scoping import parish_ids_for

    return (
        AdvisoryRequest.objects.filter(farmer__village__parish_id__in=parish_ids_for(user))
        .select_related("farmer", "farmer__village__parish")
        .order_by("-created_at")
    )
