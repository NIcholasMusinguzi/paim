from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import Role, ScopeLevel, SystemUser
from apps.farmers.models import Crop, Farmer, Season
from apps.geo.models import District, Parish, Subcounty, Village
from apps.market.models import AwardRecord, Buyer, Declaration, Grade, Lot, LotStatus, Settlement


@pytest.fixture
def world(db):
    district = District.objects.create(name="Mukono")
    subcounty = Subcounty.objects.create(district=district, name="Kyampisi")
    parish = Parish.objects.create(subcounty=subcounty, name="Katosi", lot_min_bags=5)
    other_parish = Parish.objects.create(subcounty=subcounty, name="Elsewhere")
    village = Village.objects.create(parish=parish, name="Kigunga")
    crop = Crop.objects.create(name="Maize")
    today = timezone.localdate()
    season = Season.objects.create(
        year=today.year, season_no=1,
        start_date=today - timedelta(days=10), end_date=today + timedelta(days=100))
    chief = SystemUser.objects.create_user(
        phone="+256700000090", password="pin1234", full_name="Chief",
        role=Role.PARISH_CHIEF, scope_level=ScopeLevel.PARISH, scope_id=parish.id)
    other_chief = SystemUser.objects.create_user(
        phone="+256700000091", password="pin1234", full_name="Other Chief",
        role=Role.PARISH_CHIEF, scope_level=ScopeLevel.PARISH, scope_id=other_parish.id)
    farmer = Farmer.objects.create(village=village, full_name="Grace Nabirye", sex="F", registered_by=chief)
    buyer1_user = SystemUser.objects.create_user(
        phone="+256700000092", password="pin1234", full_name="Buyer One", role=Role.BUYER,
        scope_level=ScopeLevel.NATIONAL)
    buyer1 = Buyer.objects.create(name="Buyer One Co", licence_no="LIC-1", user=buyer1_user)
    buyer2_user = SystemUser.objects.create_user(
        phone="+256700000093", password="pin1234", full_name="Buyer Two", role=Role.BUYER,
        scope_level=ScopeLevel.NATIONAL)
    buyer2 = Buyer.objects.create(name="Buyer Two Co", licence_no="LIC-2", user=buyer2_user)
    lot = Lot.objects.create(parish=parish, season=season, crop=crop, min_bags=5)
    Declaration.objects.create(farmer=farmer, lot=lot, bags=5, grade=Grade.G1, declared_via="web")
    return {"parish": parish, "other_parish": other_parish, "chief": chief, "other_chief": other_chief,
            "farmer": farmer, "buyer1": buyer1, "buyer2": buyer2, "lot": lot}


def _client(user):
    client = APIClient()
    client.post("/api/v1/auth/login/", {"phone": user.phone, "password": "pin1234"}, format="json")
    return client


@pytest.mark.django_db
def test_buyer_lists_open_lots(world):
    res = _client(world["buyer1"].user).get("/api/v1/buyer/lots/")
    assert res.status_code == 200
    assert [lot_row["id"] for lot_row in res.data] == [world["lot"].id]


@pytest.mark.django_db
def test_non_buyer_cannot_list_buyer_lots(world):
    res = _client(world["chief"]).get("/api/v1/buyer/lots/")
    assert res.status_code == 403


@pytest.mark.django_db
def test_buyer_can_only_see_own_bid_before_closure(world):
    world["lot"].status = LotStatus.OPEN
    world["lot"].save()
    c1 = _client(world["buyer1"].user)
    c1.post(f"/api/v1/lots/{world['lot'].id}/bids/", {"price_per_kg": 1200, "terms": "cash"}, format="json")
    c2 = _client(world["buyer2"].user)
    c2.post(f"/api/v1/lots/{world['lot'].id}/bids/", {"price_per_kg": 1500, "terms": "mobile money"}, format="json")

    res1 = c1.get(f"/api/v1/lots/{world['lot'].id}/")
    assert [b["price_per_kg"] for b in res1.data["bids"]] == [1200]

    res2 = c2.get(f"/api/v1/lots/{world['lot'].id}/")
    assert [b["price_per_kg"] for b in res2.data["bids"]] == [1500]


@pytest.mark.django_db
def test_bidding_after_closure_is_rejected(world):
    world["lot"].status = LotStatus.CLOSED
    world["lot"].save()
    res = _client(world["buyer1"].user).post(
        f"/api/v1/lots/{world['lot'].id}/bids/", {"price_per_kg": 1200, "terms": "cash"}, format="json")
    assert res.status_code == 409


@pytest.mark.django_db
def test_award_creates_settlement_with_grade_factor_and_charges_commission_to_buyer(world):
    bid_client = _client(world["buyer1"].user)
    bid_res = bid_client.post(f"/api/v1/lots/{world['lot'].id}/bids/",
                              {"price_per_kg": 1000, "terms": "cash"}, format="json")
    bid_id = bid_res.data["bids"][0]["id"]
    Lot.objects.filter(pk=world["lot"].id).update(status=LotStatus.CLOSED)

    res = _client(world["chief"]).post(
        f"/api/v1/lots/{world['lot'].id}/award/",
        {"bid_id": bid_id, "committee_minute_ref": "MIN-042"}, format="json")
    assert res.status_code == 200
    assert res.data["status"] == "awarded"

    world["lot"].refresh_from_db()
    assert world["lot"].status == LotStatus.AWARDED
    assert AwardRecord.objects.filter(lot=world["lot"], committee_minute_ref="MIN-042").exists()

    declaration = Declaration.objects.get(lot=world["lot"])
    settlement = Settlement.objects.get(declaration=declaration)
    # 5 bags * 100kg * 1000 UGX/kg * grade-1 factor 1.00
    assert (settlement.gross_amount, settlement.commission, settlement.net_amount) == (500_000, 7_500, 500_000)


@pytest.mark.django_db
def test_award_is_scoped_to_the_officers_own_parish(world):
    bid = _client(world["buyer1"].user).post(
        f"/api/v1/lots/{world['lot'].id}/bids/", {"price_per_kg": 1000, "terms": "cash"}, format="json")
    bid_id = bid.data["bids"][0]["id"]
    Lot.objects.filter(pk=world["lot"].id).update(status=LotStatus.CLOSED)

    res = _client(world["other_chief"]).post(
        f"/api/v1/lots/{world['lot'].id}/award/",
        {"bid_id": bid_id, "committee_minute_ref": "MIN-042"}, format="json")
    assert res.status_code == 403


@pytest.mark.django_db
def test_farmer_cannot_award(world):
    farmer_user = SystemUser.objects.create_user(
        phone="+256700000094", password="pin1234", full_name="Farmer",
        role=Role.FARMER, scope_level=ScopeLevel.PARISH, scope_id=world["parish"].id)
    res = _client(farmer_user).post(
        f"/api/v1/lots/{world['lot'].id}/award/", {"bid_id": 1, "committee_minute_ref": "x"}, format="json")
    assert res.status_code == 403
