from .models import Declaration, Lot


def open_lots():
    return Lot.objects.filter(status="open").select_related("parish", "crop", "season")


def parish_dashboard_data(parish) -> dict:
    from apps.advisory.selectors import current_season
    from apps.analytics.models import ParishSeasonMetric

    season = current_season()
    lot = (
        Lot.objects.filter(parish=parish, season=season).select_related("crop").order_by("-opened_at").first()
        if season else None
    )
    declarations = (
        Declaration.objects.filter(lot=lot).select_related("farmer").order_by("-created_at")[:50]
        if lot else Declaration.objects.none()
    )
    metrics = (
        ParishSeasonMetric.objects.filter(parish=parish, season=season, crop=lot.crop).first()
        if lot else None
    )
    return {"parish": parish, "lot": lot, "declarations": declarations, "metrics": metrics}
