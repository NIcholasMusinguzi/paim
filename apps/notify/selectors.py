from .models import Notification


def for_farmer(farmer):
    return Notification.objects.filter(farmer=farmer).order_by("-created_at")
