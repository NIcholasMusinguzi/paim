from django.db import models

from apps.core.models import TimeStampedModel


class Organisation(TimeStampedModel):
    name = models.CharField(max_length=120)
    org_type = models.CharField(max_length=24)


class Consent(TimeStampedModel):
    farmer = models.ForeignKey(
        "farmers.Farmer", on_delete=models.CASCADE, related_name="consents")
    organisation = models.ForeignKey(Organisation, on_delete=models.PROTECT)
    purpose = models.CharField(max_length=64)
    revoked_at = models.DateTimeField(null=True, blank=True)
    channel = models.CharField(max_length=16)


class AccessLog(TimeStampedModel):
    organisation = models.ForeignKey(Organisation, on_delete=models.PROTECT)
    farmer = models.ForeignKey("farmers.Farmer", on_delete=models.PROTECT)
    consent = models.ForeignKey(
        Consent, null=True, blank=True, on_delete=models.SET_NULL)
    purpose = models.CharField(max_length=64)
    outcome = models.CharField(max_length=12)
    actor = models.CharField(max_length=120)

    def save(self, *args, **kwargs):
        if self.pk:
            raise RuntimeError("AccessLog is append-only")
        return super().save(*args, **kwargs)
