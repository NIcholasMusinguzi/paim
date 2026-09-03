from decimal import Decimal

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.analytics import services as analytics_services
from apps.market.models import AwardRecord, Bid, Declaration, Grade, Lot, LotStatus, Settlement
from apps.realtime import events


class DomainError(Exception):
    pass


def grade_for(moisture):
    moisture = Decimal(moisture)
    if moisture <= Decimal(str(settings.GRADE1_MAX_MOISTURE)):
        return Grade.G1
    if moisture <= Decimal(str(settings.GRADE2_MAX_MOISTURE)):
        return Grade.G2
    return Grade.REJECT


def sellable_bags(lot):
    return sum(d.bags for d in lot.declarations.all() if d.grade != Grade.REJECT)


def pct_grade1(lot) -> int:
    sellable = sellable_bags(lot)
    if not sellable:
        return 0
    grade1 = sum(d.bags for d in lot.declarations.all() if d.grade == Grade.G1)
    return round(grade1 * 100 / sellable)


def get_or_open_lot(*, parish, crop, season):
    """The current lot for this parish/season/crop, whatever its status.
    Once it closes, further declarations are rejected (see declare()) until
    someone explicitly opens the next one — bags do not silently spill into
    a fresh lot just because the last one filled up."""
    lot = Lot.objects.filter(parish=parish, crop=crop, season=season).order_by("-opened_at").first()
    if lot:
        return lot
    return Lot.objects.create(parish=parish, crop=crop, season=season, min_bags=parish.lot_min_bags)


@transaction.atomic
def declare(*, farmer, crop, bags, moisture, actor, via):
    from apps.advisory.selectors import current_season

    if not 1 <= bags <= 200:
        raise DomainError("Bags must be between 1 and 200.")
    season = current_season()
    if season is None:
        raise DomainError("No active season.")
    lot = get_or_open_lot(parish=farmer.village.parish, crop=crop, season=season)
    if lot.status != LotStatus.OPEN:
        raise DomainError("The lot for this parish has already closed.")
    declaration = Declaration.objects.create(
        farmer=farmer, lot=lot, bags=bags,
        moisture_pct=moisture, grade=grade_for(moisture) if moisture is not None else Grade.UNGRADED,
        declared_via=via)
    lot = maybe_close_lot(lot)
    transaction.on_commit(lambda: events.publish(
        f"parish.{lot.parish_id}", "declaration.created",
        {"lot_id": lot.id, "declaration_id": declaration.id, "bags": declaration.bags,
         "grade": declaration.grade, "lot_bags": sellable_bags(lot), "lot_min_bags": lot.min_bags}))
    return declaration


@transaction.atomic
def record_grading(*, declaration_id, moisture, actor):
    declaration = Declaration.objects.select_for_update(
    ).select_related("lot").get(pk=declaration_id)
    if declaration.lot.status != LotStatus.OPEN:
        raise DomainError(
            "Cannot grade a declaration once the lot has closed.")
    declaration.moisture_pct = Decimal(moisture)
    declaration.grade = grade_for(moisture)
    declaration.graded_by = actor
    declaration.graded_at = timezone.now()
    declaration.save(update_fields=[
                     "moisture_pct", "grade", "graded_by", "graded_at", "updated_at"])
    lot = declaration.lot
    transaction.on_commit(lambda: events.publish(
        f"parish.{lot.parish_id}", "declaration.graded",
        {"declaration_id": declaration.id, "grade": declaration.grade,
         "moisture_pct": str(declaration.moisture_pct), "pct_grade1": pct_grade1(lot)}))
    return declaration


@transaction.atomic
def maybe_close_lot(lot):
    locked = Lot.objects.select_for_update().get(pk=lot.pk)
    if locked.status != LotStatus.OPEN or sellable_bags(locked) < locked.min_bags:
        return locked
    locked.status = LotStatus.CLOSED
    locked.closed_at = timezone.now()
    locked.save(update_fields=["status", "closed_at", "updated_at"])
    Bid.objects.filter(lot=locked).update(sealed_until=locked.closed_at)
    bags, bid_count = sellable_bags(locked), locked.bids.count()
    bids = [{"buyer_name": b.buyer.name, "price_per_kg": b.price_per_kg, "terms": b.terms}
            for b in locked.bids.select_related("buyer").order_by("-price_per_kg")]
    transaction.on_commit(lambda: events.publish(
        f"parish.{locked.parish_id}", "lot.closed",
        {"lot_id": locked.id, "bags": bags, "bid_count": bid_count}))
    transaction.on_commit(lambda: events.publish(
        f"parish.{locked.parish_id}", "bid.disclosed", {"lot_id": locked.id, "bids": bids}))
    transaction.on_commit(lambda: analytics_services.recompute_parish_metric(
        parish_id=locked.parish_id, season_id=locked.season_id, crop_id=locked.crop_id))
    return locked


def submit_bid(*, lot, buyer, price_per_kg, terms):
    if lot.status != LotStatus.OPEN:
        raise DomainError("Bidding is closed for this lot.")
    bid = Bid.objects.create(lot=lot, buyer=buyer, price_per_kg=price_per_kg, terms=terms)
    transaction.on_commit(lambda: events.publish(
        f"parish.{lot.parish_id}", "bid.received", {"lot_id": lot.id, "bid_count": lot.bids.count()}))
    return bid


@transaction.atomic
def award_lot(*, lot_id, bid_id, actor, minute_ref):
    lot = Lot.objects.select_for_update().get(pk=lot_id)
    if lot.status != LotStatus.CLOSED:
        raise DomainError("Only a closed lot can be awarded.")
    bid = lot.bids.get(pk=bid_id)
    lot.awarded_bid, lot.status = bid, LotStatus.AWARDED
    lot.save(update_fields=["awarded_bid", "status", "updated_at"])
    AwardRecord.objects.create(lot=lot, bid=bid, recorded_by=actor, committee_minute_ref=minute_ref)

    lot_value = 0
    for declaration in lot.declarations.exclude(grade=Grade.REJECT):
        gross, commission, net = settlement_amounts(declaration, bid)
        Settlement.objects.create(declaration=declaration, bid=bid,
                                  gross_amount=gross, commission=commission, net_amount=net)
        lot_value += gross

    transaction.on_commit(lambda: events.publish(
        f"parish.{lot.parish_id}", "lot.awarded",
        {"lot_id": lot.id, "buyer_name": bid.buyer.name, "price_per_kg": bid.price_per_kg,
         "lot_value": lot_value}))
    transaction.on_commit(lambda: analytics_services.recompute_parish_metric(
        parish_id=lot.parish_id, season_id=lot.season_id, crop_id=lot.crop_id))
    return lot


def visible_bids(lot, viewer):
    if lot.status in (LotStatus.CLOSED, LotStatus.AWARDED, LotStatus.SETTLED):
        return lot.bids.select_related("buyer").order_by("-price_per_kg")
    if getattr(viewer, "role", None) == "buyer":
        return lot.bids.filter(buyer__user=viewer)
    return Bid.objects.none()


GRADE_FACTOR = {Grade.G1: Decimal("1.00"), Grade.G2: Decimal(
    "0.88"), Grade.REJECT: Decimal(0)}


def settlement_amounts(declaration, bid):
    gross = int(Decimal(bid.price_per_kg * declaration.bags * 100)
                * GRADE_FACTOR[declaration.grade])
    commission = int(gross * Decimal(str(settings.BUYER_COMMISSION_PCT)) / 100)
    return gross, commission, gross
