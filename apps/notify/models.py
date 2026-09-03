from django.db import models

from apps.core.models import TimeStampedModel


class Notification(TimeStampedModel):
    farmer = models.ForeignKey("farmers.Farmer", on_delete=models.CASCADE)
    channel = models.CharField(max_length=16, default="console")
    template = models.CharField(max_length=64)
    body = models.TextField()
    provider_ref = models.CharField(max_length=120, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
