from decimal import Decimal

import pytest
from django.utils import timezone

from apps.accounts.models import Role, ScopeLevel, SystemUser
from apps.consent.models import AccessLog, Consent, Organisation
from apps.consent.services import ConsentRefused, read_farmer_data
from apps.farmers.models import Crop, Farmer, Season
from apps.geo.models import District, Parish, Subcounty, Village
from apps.market.models import Bid, Buyer, Declaration, Grade, Lot, LotStatus
from apps.market.services import grade_for, maybe_close_lot, settlement_amounts, visible_bids


@pytest.fixture
def data(db):
    district = District.objects.create(name="Mukono")
    subcounty = Subcounty.objects.create(district=district, name="Kyampisi")
    parish = Parish.objects.create(
        subcounty=subcounty, name="Katosi", lot_min_bags=10)
    village = Village.objects.create(parish=parish, name="Kigunga")
    user = SystemUser.objects.create_user(phone="+256700000001", password="pin", full_name="Agent",
                                          role=Role.AGENT, scope_level=ScopeLevel.PARISH, scope_id=parish.id)
    farmer = Farmer.objects.create(
        village=village, full_name="Grace Nabirye", sex="F", registered_by=user)
    crop = Crop.objects.create(name="Maize")
    season = Season.objects.create(year=2026, season_no=1, start_date=timezone.localdate(
    ).replace(month=1, day=1), end_date=timezone.localdate().replace(month=12, day=31))
    lot = Lot.objects.create(
        parish=parish, season=season, crop=crop, min_bags=10)
    return {"parish": parish, "user": user, "farmer": farmer, "crop": crop, "season": season, "lot": lot}


def test_grade_boundaries():
    assert grade_for(Decimal("13.0")) == Grade.G1
    assert grade_for(Decimal("15.0")) == Grade.G2
    assert grade_for(Decimal("15.1")) == Grade.REJECT


@pytest.mark.django_db
def test_lot_closes_and_seals_bids(data):
    declaration = Declaration.objects.create(
        farmer=data["farmer"], lot=data["lot"], bags=10, grade=Grade.G1, declared_via="web")
    buyer_user = SystemUser.objects.create_user(
        phone="+256700000002", full_name="Buyer", role=Role.BUYER, scope_level=ScopeLevel.NATIONAL)
    buyer = Buyer.objects.create(
        name="Buyer Co", licence_no="LIC-1", user=buyer_user)
    bid = Bid.objects.create(
        lot=data["lot"], buyer=buyer, price_per_kg=1200, terms="cash")
    closed = maybe_close_lot(data["lot"])
    assert declaration.lot_id == closed.id
    assert closed.status == LotStatus.CLOSED
    assert Bid.objects.get(pk=bid.pk).sealed_until is not None
    assert visible_bids(closed, data["farmer"]).count() == 1


@pytest.mark.django_db
def test_settlement_commission_does_not_reduce_farmer_amount(data):
    declaration = Declaration.objects.create(
        farmer=data["farmer"], lot=data["lot"], bags=2, grade=Grade.G2, declared_via="web")
    buyer = Buyer.objects.create(name="Buyer Co", licence_no="LIC-2", user=SystemUser.objects.create_user(
        phone="+256700000003", full_name="Buyer", role=Role.BUYER, scope_level=ScopeLevel.NATIONAL))
    gross, commission, net = settlement_amounts(declaration, Bid(
        lot=data["lot"], buyer=buyer, price_per_kg=1000, terms="cash"))
    assert (gross, commission, net) == (176000, 2640, 176000)


@pytest.mark.django_db
def test_consent_refusal_is_logged(data):
    organisation = Organisation.objects.create(name="SACCO", org_type="sacco")
    with pytest.raises(ConsentRefused):
        read_farmer_data(farmer=data["farmer"], organisation=organisation,
                         purpose="history", actor="sacco", fields=["full_name"])
    assert AccessLog.objects.get().outcome == "refused"
    Consent.objects.create(
        farmer=data["farmer"], organisation=organisation, purpose="history", channel="web")
    assert read_farmer_data(farmer=data["farmer"], organisation=organisation, purpose="history", actor="sacco", fields=[
                            "full_name"])["full_name"] == "Grace Nabirye"
    assert AccessLog.objects.filter(outcome="allowed").exists()
    with pytest.raises(RuntimeError):
        AccessLog.objects.get(outcome="allowed").save()
