from django.db import models

from apps.accounts.models import ScopeLevel
from apps.core.models import TimeStampedModel


class ParishSeasonMetric(TimeStampedModel):
    parish = models.ForeignKey("geo.Parish", on_delete=models.CASCADE)
    season = models.ForeignKey("farmers.Season", on_delete=models.CASCADE)
    crop = models.ForeignKey("farmers.Crop", on_delete=models.CASCADE)
    farmers_registered = models.PositiveIntegerField(default=0)
    farmers_active = models.PositiveIntegerField(default=0)
    bags_declared = models.PositiveIntegerField(default=0)
    pct_grade1 = models.PositiveSmallIntegerField(default=0)
    avg_price_per_kg = models.PositiveIntegerField(null=True)
    computed_at = models.DateTimeField()

    class Meta:
        constraints = [models.UniqueConstraint(
            fields=["parish", "season", "crop"], name="unique_parish_metric")]


class DistrictSeasonMetric(TimeStampedModel):
    """Mirrors ParishSeasonMetric, keyed on district/season/crop. Rows are
    volume-weighted rollups of ParishSeasonMetric, never a mean of means
    (IMPLEMENTATION.md section 7.5) — dashboards read this table, they
    MUST NOT aggregate Declaration or ParishSeasonMetric at request time."""

    district = models.ForeignKey("geo.District", on_delete=models.CASCADE)
    season = models.ForeignKey("farmers.Season", on_delete=models.CASCADE)
    crop = models.ForeignKey("farmers.Crop", on_delete=models.CASCADE)
    farmers_registered = models.PositiveIntegerField(default=0)
    farmers_active = models.PositiveIntegerField(default=0)
    bags_declared = models.PositiveIntegerField(default=0)
    pct_grade1 = models.PositiveSmallIntegerField(default=0)
    avg_price_per_kg = models.PositiveIntegerField(null=True)
    parishes_reporting = models.PositiveIntegerField(default=0)
    rank_national = models.PositiveSmallIntegerField(null=True, blank=True)
    computed_at = models.DateTimeField()

    class Meta:
        constraints = [models.UniqueConstraint(
            fields=["district", "season", "crop"], name="unique_district_metric")]


class NationalSeasonMetric(TimeStampedModel):
    season = models.ForeignKey("farmers.Season", on_delete=models.CASCADE)
    crop = models.ForeignKey("farmers.Crop", on_delete=models.CASCADE)
    farmers_registered = models.PositiveIntegerField(default=0)
    farmers_active = models.PositiveIntegerField(default=0)
    bags_declared = models.PositiveIntegerField(default=0)
    pct_grade1 = models.PositiveSmallIntegerField(default=0)
    avg_price_per_kg = models.PositiveIntegerField(null=True)
    districts_reporting = models.PositiveIntegerField(default=0)
    computed_at = models.DateTimeField()

    class Meta:
        constraints = [models.UniqueConstraint(
            fields=["season", "crop"], name="unique_national_metric")]


class TrendInsight(TimeStampedModel):
    scope_level = models.CharField(max_length=16, choices=ScopeLevel.choices)
    scope_id = models.PositiveIntegerField(null=True)
    crop = models.ForeignKey("farmers.Crop", on_delete=models.PROTECT)
    metric = models.CharField(max_length=48)
    direction = models.CharField(max_length=8, choices=[("up", "Up"), ("down", "Down"), ("flat", "Flat")])
    magnitude = models.DecimalField(max_digits=6, decimal_places=2)
    window_weeks = models.PositiveSmallIntegerField()
    message = models.TextField(max_length=600)
    approved_by = models.ForeignKey(
        "accounts.SystemUser", null=True, blank=True, on_delete=models.PROTECT)
    published_at = models.DateTimeField(null=True, blank=True)
