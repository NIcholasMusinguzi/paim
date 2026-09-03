from django.core.exceptions import PermissionDenied
from django.utils import timezone

from apps.consent.models import AccessLog, Consent


class ConsentRefused(PermissionDenied):
    pass


def read_farmer_data(*, farmer, organisation, purpose, actor, fields):
    consent = Consent.objects.filter(
        farmer=farmer, organisation=organisation, purpose=purpose, revoked_at__isnull=True).first()
    AccessLog.objects.create(organisation=organisation, farmer=farmer, consent=consent,
                             purpose=purpose, actor=actor, outcome="allowed" if consent else "refused")
    if not consent:
        raise ConsentRefused(
            f"No active consent for {organisation} / {purpose}.")
    return {field: getattr(farmer, field) for field in fields if hasattr(farmer, field)}


def revoke(*, consent_id, farmer):
    consent = Consent.objects.get(
        pk=consent_id, farmer=farmer, revoked_at__isnull=True)
    consent.revoked_at = timezone.now()
    consent.save(update_fields=["revoked_at", "updated_at"])
    return consent
