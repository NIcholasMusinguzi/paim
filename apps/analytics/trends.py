from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from apps.accounts.models import Role, ScopeLevel
from apps.advisory.services import record_delivery
from apps.realtime import events

from .models import TrendInsight

# Note: the statistical rule engine that drafts TrendInsight rows
# (IMPLEMENTATION.md section 7.6 — PriceAfterPeakHarvest, GradingPremiumGap,
# MoistureOutlier, ActiveUseDecline) is out of scope here. This module is
# the approval workflow only: insights arrive as drafts (however they were
# created) and this is the one path that can ever make one visible to a
# farmer.


class TrendApprovalError(Exception):
    pass


def farmers_for_trend_scope(insight: TrendInsight):
    from apps.farmers.models import Farmer
    from apps.farmers.selectors import farmers_for_parishes
    from apps.geo.models import Parish

    if insight.scope_level == ScopeLevel.PARISH:
        return farmers_for_parishes([insight.scope_id])
    if insight.scope_level == ScopeLevel.DISTRICT:
        parish_ids = Parish.objects.filter(subcounty__district_id=insight.scope_id).values_list("id", flat=True)
        return farmers_for_parishes(parish_ids)
    return Farmer.objects.all()


def pending_insights_for(user):
    """Insights an officer may act on: national-scope, or within their own
    district (the natural approval hierarchy — a district officer approves
    what concerns their district or a parish inside it)."""
    qs = TrendInsight.objects.filter(published_at__isnull=True).select_related("crop")
    if user.role == Role.NATIONAL_ADMIN:
        return qs
    from apps.geo.models import Parish

    parish_ids = list(Parish.objects.filter(subcounty__district_id=user.scope_id).values_list("id", flat=True))
    return qs.filter(
        Q(scope_level=ScopeLevel.NATIONAL)
        | Q(scope_level=ScopeLevel.DISTRICT, scope_id=user.scope_id)
        | Q(scope_level=ScopeLevel.PARISH, scope_id__in=parish_ids)
    )


@transaction.atomic
def approve_insight(*, insight_id, actor) -> TrendInsight:
    """A TrendInsight is never delivered until approved (MUST). Sets
    approved_by and published_at, and delivers it to every farmer in scope.
    There is no other code path that sends an unapproved insight
    (IMPLEMENTATION.md section 7.6)."""
    if actor.role not in (Role.DISTRICT_OFFICER, Role.NATIONAL_ADMIN):
        raise TrendApprovalError("Only a district officer or national admin may approve an insight.")

    insight = TrendInsight.objects.select_for_update().select_related("crop").get(pk=insight_id)
    if insight.published_at is not None:
        raise TrendApprovalError("This insight has already been published.")

    insight.approved_by = actor
    insight.published_at = timezone.now()
    insight.save(update_fields=["approved_by", "published_at", "updated_at"])

    for farmer in farmers_for_trend_scope(insight):
        record_delivery(farmer=farmer, trend=insight, channel=farmer.reach_channel)

    transaction.on_commit(lambda: events.publish(
        "scope.national.", "trend.published",
        {"insight_id": insight.id, "scope_level": insight.scope_level, "scope_id": insight.scope_id,
         "message": insight.message}))
    return insight
