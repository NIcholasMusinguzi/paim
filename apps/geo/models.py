from django.db import models

from apps.core.models import TimeStampedModel


class District(TimeStampedModel):
    name = models.CharField(max_length=64, unique=True)
    region = models.CharField(max_length=32, default="Central")


class Subcounty(TimeStampedModel):
    district = models.ForeignKey(
        District, on_delete=models.PROTECT, related_name="subcounties")
    name = models.CharField(max_length=64)

    class Meta:
        constraints = [models.UniqueConstraint(
            fields=["district", "name"], name="unique_subcounty")]


class Parish(TimeStampedModel):
    subcounty = models.ForeignKey(
        Subcounty, on_delete=models.PROTECT, related_name="parishes")
    name = models.CharField(max_length=64)
    agro_zone = models.CharField(
        max_length=32, default="Lake Victoria Crescent")
    lot_min_bags = models.PositiveIntegerField(default=800)

    @property
    def district(self):
        return self.subcounty.district


class Village(TimeStampedModel):
    parish = models.ForeignKey(
        Parish, on_delete=models.PROTECT, related_name="villages")
    name = models.CharField(max_length=64)
