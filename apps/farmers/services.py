import hashlib

from django.conf import settings
from django.db import transaction

from .models import Crop, Farmer, Planting, Plot


class SignupError(Exception):
    pass


class FarmerError(Exception):
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


@transaction.atomic
def set_current_crops(*, farmer, crop_ids, planting_date=None, area_acres=None):
    """Replace this season's plantings with the given crops. One farmer can
    grow several crops; they share a plot. An empty list clears them."""
    from django.utils import timezone

    from apps.advisory.selectors import current_season

    season = current_season()
    if season is None:
        raise FarmerError("There is no active season to update farm details.")
    wanted = list(crop_ids)
    known = set(Crop.objects.filter(pk__in=wanted).values_list("id", flat=True))
    if any(cid not in known for cid in wanted):
        raise FarmerError("Unknown crop.")

    plot = farmer.plots.order_by("id").first()
    if plot is None:
        plot = Plot.objects.create(
            farmer=farmer, area_acres=area_acres if area_acres is not None else "1.00")
    elif area_acres is not None:
        plot.area_acres = area_acres
        plot.save(update_fields=["area_acres", "updated_at"])

    date = planting_date or timezone.localdate()
    existing = {
        row.crop_id: row
        for row in Planting.objects.filter(plot__farmer=farmer, season=season)
    }
    for crop_id in wanted:
        planting = existing.get(crop_id)
        if planting is None:
            Planting.objects.create(plot=plot, season=season, crop_id=crop_id, planting_date=date)
        elif planting_date is not None:
            planting.planting_date = planting_date
            planting.save(update_fields=["planting_date", "updated_at"])
    Planting.objects.filter(plot__farmer=farmer, season=season).exclude(crop_id__in=wanted).delete()
    if hasattr(farmer, "_prefetched_objects_cache"):
        farmer._prefetched_objects_cache.pop("plots", None)
    return farmer


def hash_nin(nin):
    return hashlib.sha256(f"{nin}{settings.NIN_PEPPER}".encode()).hexdigest()


def set_nin(*, farmer, nin, consent):
    farmer.nin_consent = consent
    farmer.nin_hash = hash_nin(nin) if consent else None
    farmer.save(update_fields=["nin_consent", "nin_hash", "updated_at"])
    return farmer
