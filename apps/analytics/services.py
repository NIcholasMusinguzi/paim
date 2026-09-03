from django.db.models import Count, Q, Sum
from django.utils import timezone

from apps.farmers.models import Farmer
from apps.market.models import Declaration, Grade, Lot, LotStatus
from apps.realtime import events

from .models import DistrictSeasonMetric, NationalSeasonMetric, ParishSeasonMetric
from .serializers import DistrictMetricSerializer, NationalMetricSerializer


def pct(numerator: int, denominator: int) -> int:
    return round(numerator * 100 / denominator) if denominator else 0


def weighted(rows, value_field: str, weight_field: str = "bags_declared"):
    """Volume-weighted average, never a mean of means (IMPLEMENTATION.md
    section 7.5) — a district with one large parish and one tiny one is not
    the simple average of their two prices. Rows with no value (e.g. a
    parish that has not had a lot awarded yet) are excluded from both the
    numerator and the weight, not just the numerator — otherwise an
    all-None column would compute to 0 instead of "no data"."""
    valued = [r for r in rows if getattr(r, value_field) is not None]
    total_weight = sum(getattr(r, weight_field) for r in valued)
    if not total_weight:
        return None
    weighted_sum = sum(getattr(r, value_field) * getattr(r, weight_field) for r in valued)
    return round(weighted_sum / total_weight)


def recompute_parish_metric(*, parish_id, season_id, crop_id):
    from apps.geo.models import Parish

    declarations = Declaration.objects.filter(
        lot__parish_id=parish_id, lot__season_id=season_id, lot__crop_id=crop_id).exclude(grade=Grade.REJECT)
    # Output aliases must not shadow the "bags" field name — Django resolves
    # aggregate() kwargs against the same annotated queryset, so an alias
    # named "bags" makes the second Sum("bags", ...) resolve against the
    # first aggregate instead of the raw column and raises FieldError.
    aggregate = declarations.aggregate(total_bags=Sum("bags"), g1_bags=Sum(
        "bags", filter=Q(grade=Grade.G1)), active=Count("farmer", distinct=True))
    bags = aggregate["total_bags"] or 0
    registered = Farmer.objects.filter(village__parish_id=parish_id).count()
    awarded_lot = (
        Lot.objects.filter(parish_id=parish_id, season_id=season_id, crop_id=crop_id,
                           status__in=[LotStatus.AWARDED, LotStatus.SETTLED], awarded_bid__isnull=False)
        .select_related("awarded_bid").order_by("-closed_at").first()
    )
    row, _ = ParishSeasonMetric.objects.update_or_create(
        parish_id=parish_id, season_id=season_id, crop_id=crop_id,
        defaults={
            "farmers_registered": registered,
            "farmers_active": aggregate["active"] or 0,
            "bags_declared": bags,
            "pct_grade1": pct(aggregate["g1_bags"] or 0, bags),
            "avg_price_per_kg": awarded_lot.awarded_bid.price_per_kg if awarded_lot else None,
            "computed_at": timezone.now(),
        })
    district_id = Parish.objects.get(pk=parish_id).subcounty.district_id
    rollup_district(district_id=district_id, season_id=season_id, crop_id=crop_id)
    return row


def rollup_district(*, district_id, season_id, crop_id):
    rows = list(ParishSeasonMetric.objects.filter(
        parish__subcounty__district_id=district_id, season_id=season_id, crop_id=crop_id))
    row, _ = DistrictSeasonMetric.objects.update_or_create(
        district_id=district_id, season_id=season_id, crop_id=crop_id,
        defaults={
            "farmers_registered": sum(r.farmers_registered for r in rows),
            "farmers_active": sum(r.farmers_active for r in rows),
            "bags_declared": sum(r.bags_declared for r in rows),
            "pct_grade1": weighted(rows, "pct_grade1") or 0,
            "avg_price_per_kg": weighted(rows, "avg_price_per_kg"),
            "parishes_reporting": len(rows),
            "computed_at": timezone.now(),
        })
    row.refresh_from_db()
    events.publish(f"scope.district.{district_id}", "metrics.district", DistrictMetricSerializer(row).data)
    events.publish("scope.national.", "metrics.district", DistrictMetricSerializer(row).data)
    rollup_national(season_id=season_id, crop_id=crop_id)
    return row


def rollup_national(*, season_id, crop_id):
    rows = list(DistrictSeasonMetric.objects.filter(season_id=season_id, crop_id=crop_id))
    # Ranked on average price: the whole point of the national dashboard is
    # price transparency across districts (the "so what" a district officer
    # or national admin looks at first).
    for rank, r in enumerate(
        sorted(rows, key=lambda r: (r.avg_price_per_kg is None, -(r.avg_price_per_kg or 0))), start=1,
    ):
        if r.rank_national != rank:
            DistrictSeasonMetric.objects.filter(pk=r.pk).update(rank_national=rank)

    row, _ = NationalSeasonMetric.objects.update_or_create(
        season_id=season_id, crop_id=crop_id,
        defaults={
            "farmers_registered": sum(r.farmers_registered for r in rows),
            "farmers_active": sum(r.farmers_active for r in rows),
            "bags_declared": sum(r.bags_declared for r in rows),
            "pct_grade1": weighted(rows, "pct_grade1") or 0,
            "avg_price_per_kg": weighted(rows, "avg_price_per_kg"),
            "districts_reporting": len(rows),
            "computed_at": timezone.now(),
        })
    events.publish("scope.national.", "metrics.national", NationalMetricSerializer(row).data)
    return row
