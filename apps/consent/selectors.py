from .models import AccessLog, Consent


def active_consent(farmer, organisation, purpose):
    return Consent.objects.filter(farmer=farmer, organisation=organisation, purpose=purpose, revoked_at__isnull=True).first()


def access_history(farmer):
    return AccessLog.objects.filter(farmer=farmer).order_by("-created_at")
