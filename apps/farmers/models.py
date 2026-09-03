from django.db import models

from apps.core.models import TimeStampedModel


class Crop(TimeStampedModel):
    name = models.CharField(max_length=48, unique=True)
    cycle_weeks = models.PositiveSmallIntegerField(default=14)


class Season(TimeStampedModel):
    year = models.PositiveSmallIntegerField()
    season_no = models.PositiveSmallIntegerField(choices=[(1, "A"), (2, "B")])
    start_date = models.DateField()
    end_date = models.DateField()

    class Meta:
        constraints = [models.UniqueConstraint(
            fields=["year", "season_no"], name="unique_season")]


class Farmer(TimeStampedModel):
    village = models.ForeignKey(
        "geo.Village", on_delete=models.PROTECT, related_name="farmers")
    full_name = models.CharField(max_length=120)
    sex = models.CharField(max_length=1, choices=[
                           ("F", "Female"), ("M", "Male")])
    birth_year = models.PositiveSmallIntegerField(null=True, blank=True)
    phone = models.CharField(max_length=20, null=True,
                             blank=True, db_index=True)
    language = models.CharField(max_length=16, default="lug")
    reach_channel = models.CharField(max_length=16, default="agent")
    nin_hash = models.CharField(
        max_length=64, null=True, blank=True, db_index=True)
    nin_consent = models.BooleanField(default=False)
    # Null means self-registered (the farmer signed up directly rather than
    # being registered by an agent).
    registered_by = models.ForeignKey(
        "accounts.SystemUser", null=True, blank=True, on_delete=models.PROTECT)
    user = models.OneToOneField(
        "accounts.SystemUser", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="farmer_profile")


class Plot(TimeStampedModel):
    farmer = models.ForeignKey(
        Farmer, on_delete=models.CASCADE, related_name="plots")
    area_acres = models.DecimalField(max_digits=5, decimal_places=2)
    gps_point = models.CharField(max_length=64, null=True, blank=True)


class Planting(TimeStampedModel):
    plot = models.ForeignKey(
        Plot, on_delete=models.CASCADE, related_name="plantings")
    season = models.ForeignKey(Season, on_delete=models.PROTECT)
    crop = models.ForeignKey(Crop, on_delete=models.PROTECT)
    planting_date = models.DateField()
    variety = models.CharField(max_length=64, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(
            fields=["plot", "season", "crop"], name="unique_planting")]
