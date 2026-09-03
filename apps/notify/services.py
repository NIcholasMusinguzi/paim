from django.utils import timezone

from .models import Notification


def queue(*, farmer, template, body, channel="console"):
    return Notification.objects.create(farmer=farmer, template=template, body=body, channel=channel, sent_at=timezone.now())
