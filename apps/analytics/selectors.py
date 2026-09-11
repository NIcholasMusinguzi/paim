from apps.accounts.scoping import parish_ids_for
from apps.analytics.models import DistrictSeasonMetric, ParishSeasonMetric
from apps.analytics.services import pct
from apps.geo.models import Parish
from apps.market.models import Lot, LotStatus


def district_in_scope(user, district_id) -> bool:
    return Parish.objects.filter(
        id__in=parish_ids_for(user), subcounty__district_id=district_id).exists()


def parish_comparison(user, *, district_id, season_id, crop_id) -> list[dict]:
    parish_ids = list(
        Parish.objects.filter(id__in=parish_ids_for(user), subcounty__district_id=district_id)
        .order_by("name")
        .values_list("id", "name")
    )
    metrics = {
        row.parish_id: row
        for row in ParishSeasonMetric.objects.filter(
            parish_id__in=[pid for pid, _ in parish_ids], season_id=season_id, crop_id=crop_id)
    }
    live = set(
        Lot.objects.filter(
            parish_id__in=[pid for pid, _ in parish_ids],
            season_id=season_id, crop_id=crop_id, status=LotStatus.OPEN,
        ).values_list("parish_id", flat=True)
    )
    rows = []
    for parish_id, name in parish_ids:
        metric = metrics.get(parish_id)
        registered = metric.farmers_registered if metric else 0
        active = metric.farmers_active if metric else 0
        rows.append({
            "id": metric.id if metric else parish_id,
            "parish_id": parish_id,
            "parish": name,
            "farmers_registered": registered,
            "farmers_active": active,
            "bags_declared": metric.bags_declared if metric else 0,
            "pct_grade1": metric.pct_grade1 if metric else 0,
            "avg_price_per_kg": metric.avg_price_per_kg if metric else None,
            "agent_reach": pct(active, registered),
            "live": parish_id in live,
            "computed_at": metric.computed_at if metric else None,
        })
    return rows


def district_season_bars(*, district_id, crop_id, limit=3) -> list[dict]:
    rows = list(
        DistrictSeasonMetric.objects.filter(district_id=district_id, crop_id=crop_id)
        .select_related("season")
        .order_by("-season__year", "-season__season_no")[:limit]
    )
    rows.reverse()
    return [{
        "season_id": row.season_id,
        "label": f"{row.season.year} {'A' if row.season.season_no == 1 else 'B'}",
        "pct_grade1": row.pct_grade1,
        "avg_price_per_kg": row.avg_price_per_kg,
    } for row in rows]
