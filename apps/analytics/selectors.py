from .models import ParishSeasonMetric


def parish_metrics(*, season_id, crop_id, parish_ids=None):
    query = ParishSeasonMetric.objects.filter(
        season_id=season_id, crop_id=crop_id)
    return query.filter(parish_id__in=parish_ids) if parish_ids is not None else query
