from django.db.models import Q

from apps.accounts.models import ScopeLevel
from apps.advisory.selectors import advice_for, current_season
from apps.analytics.models import ParishSeasonMetric, TrendInsight
from apps.market.models import Declaration, Lot

from .models import Farmer, Planting


def farmers_for_parishes(parish_ids):
    return Farmer.objects.filter(village__parish_id__in=parish_ids).select_related("village")


def farmer_home(farmer: Farmer) -> dict:
    """Everything the farmer route needs in one read, composed here rather
    than as five client round trips (IMPLEMENTATION_REACT.md section 4.1).
    Weather is served from GET /api/v1/weather/ (Open-Meteo), not this payload."""
    parish = farmer.village.parish
    season = current_season()
    crop_ids = list(
        Planting.objects.filter(plot__farmer=farmer, season=season)
        .values_list("crop_id", flat=True).distinct()
    ) if season else []

    lots = (
        Lot.objects.filter(parish=parish, season=season, crop_id__in=crop_ids).select_related("crop")
        if season and crop_ids else Lot.objects.none()
    )
    prices = (
        ParishSeasonMetric.objects.filter(
            parish=parish, season=season, crop_id__in=crop_ids, avg_price_per_kg__isnull=False,
        ).select_related("crop")
        if season and crop_ids else ParishSeasonMetric.objects.none()
    )
    declarations = (
        Declaration.objects.filter(farmer=farmer)
        .select_related("lot", "lot__crop")
        .order_by("-created_at")[:5]
    )
    trends = (
        TrendInsight.objects.filter(published_at__isnull=False)
        .filter(
            Q(scope_level=ScopeLevel.PARISH, scope_id=parish.id)
            | Q(scope_level=ScopeLevel.DISTRICT, scope_id=parish.subcounty.district_id)
            | Q(scope_level=ScopeLevel.NATIONAL)
        )
        .select_related("crop")
        .order_by("-published_at")[:5]
    )

    return {
        "farmer": farmer,
        "advice": advice_for(farmer),
        "lots": lots,
        "prices": prices,
        "declarations": declarations,
        "trends": trends,
    }
