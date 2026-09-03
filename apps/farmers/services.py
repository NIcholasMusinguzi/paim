import hashlib

from django.conf import settings
from django.db import transaction

from .models import Farmer, Planting, Plot


class SignupError(Exception):
    pass


@transaction.atomic
def sign_up_farmer(*, phone, password, full_name, sex, village, language="lug"):
    """Self-service registration: a farmer creates their own login rather
    than an agent registering them (registered_by is left null). Reuses the
    same name+village+phone dedup rule as agent registration, so signing up
    a second time with the same details links to the existing profile
    instead of creating a duplicate — and the account still gets attached."""
    from apps.accounts.models import Role, ScopeLevel, SystemUser

    if SystemUser.objects.filter(phone=phone).exists():
        raise SignupError("An account with this phone number already exists. Try signing in instead.")

    user = SystemUser.objects.create_user(
        phone=phone, password=password, full_name=full_name,
        role=Role.FARMER, scope_level=ScopeLevel.PARISH, scope_id=village.parish_id)
    farmer, _ = register_farmer(
        full_name=full_name, village=village, sex=sex, registered_by=None,
        language=language, reach_channel="web", phone=phone)
    farmer.user = user
    farmer.save(update_fields=["user"])
    return user


@transaction.atomic
def register_farmer(*, full_name, village, sex, registered_by, language="lug", reach_channel="agent",
                     phone=None, crop=None, planting_date=None, area_acres=None, season=None):
    """Registers a farmer, or returns the existing one if this is a retried
    offline registration. A farmer created offline (same name + village +
    phone) already exists MUST return the existing record, never a
    duplicate (IMPLEMENTATION.md section 9, conflict rules)."""
    existing = Farmer.objects.filter(full_name=full_name, village=village, phone=phone).first()
    if existing:
        return existing, False
    farmer = Farmer.objects.create(
        village=village, full_name=full_name, sex=sex, language=language,
        reach_channel=reach_channel, phone=phone, registered_by=registered_by)
    if crop and planting_date and area_acres is not None and season:
        plot = Plot.objects.create(farmer=farmer, area_acres=area_acres)
        Planting.objects.create(plot=plot, season=season, crop=crop, planting_date=planting_date)
    return farmer, True


def hash_nin(nin):
    return hashlib.sha256(f"{nin}{settings.NIN_PEPPER}".encode()).hexdigest()


def set_nin(*, farmer, nin, consent):
    farmer.nin_consent = consent
    farmer.nin_hash = hash_nin(nin) if consent else None
    farmer.save(update_fields=["nin_consent", "nin_hash", "updated_at"])
    return farmer
