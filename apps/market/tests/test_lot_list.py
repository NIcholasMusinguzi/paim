from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import Role, ScopeLevel, SystemUser
from apps.farmers.models import Crop, Farmer, Season
from apps.geo.models import District, Parish, Subcounty, Village
from apps.market.models import Buyer, Declaration, Grade, Lot, LotStatus
from apps.market.services import submit_bid


@pytest.fixture
def world(db):
    district = District.objects.create(name="Mukono")
    subcounty = Subcounty.objects.create(district=district, name="Kyampisi")
    parish = Parish.objects.create(subcounty=subcounty, name="Katosi", lot_min_bags=5)
    other = Parish.objects.create(subcounty=subcounty, name="Elsewhere")
    village = Village.objects.create(parish=parish, name="Kigunga")
    crop = Crop.objects.create(name="Maize")
    today = timezone.localdate()
    season = Season.objects.create(
        year=today.year, season_no=1,
        start_date=today - timedelta(days=10), end_date=today + timedelta(days=100))
    chief = SystemUser.objects.create_user(
        phone="+256700000190", password="pin1234", full_name="Chief",
        role=Role.PARISH_CHIEF, scope_level=ScopeLevel.PARISH, scope_id=parish.id)
    other_chief = SystemUser.objects.create_user(
        phone="+256700000191", password="pin1234", full_name="Other",
        role=Role.PARISH_CHIEF, scope_level=ScopeLevel.PARISH, scope_id=other.id)
    farmer_user = SystemUser.objects.create_user(
        phone="+256700000194", password="pin1234", full_name="Grace",
        role=Role.FARMER, scope_level=ScopeLevel.PARISH, scope_id=parish.id)
    farmer = Farmer.objects.create(
        village=village, full_name="Grace Nabirye", sex="F", registered_by=chief, user=farmer_user)
    buyer_user = SystemUser.objects.create_user(
        phone="+256700000192", password="pin1234", full_name="Buyer",
        role=Role.BUYER, scope_level=ScopeLevel.NATIONAL)
    buyer = Buyer.objects.create(name="Buyer Co", licence_no="LIC-L", user=buyer_user)
    lot = Lot.objects.create(parish=parish, season=season, crop=crop, min_bags=5)
    Declaration.objects.create(farmer=farmer, lot=lot, bags=5, grade=Grade.G1, declared_via="web")
    return {
        "parish": parish, "chief": chief, "other_chief": other_chief,
        "farmer_user": farmer_user, "buyer": buyer, "lot": lot,
    }


def _client(user):
    client = APIClient()
    client.post("/api/v1/auth/login/", {"phone": user.phone, "password": "pin1234"}, format="json")
    return client


@pytest.mark.django_db
def test_scoped_users_list_lots_in_their_parish(world):
    submit_bid(lot=world["lot"], buyer=world["buyer"], price_per_kg=1100, terms="cash")
    chief_res = _client(world["chief"]).get("/api/v1/lots/")
    assert chief_res.status_code == 200
    assert chief_res.data[0]["bid_count"] == 1
    assert chief_res.data[0]["bids"] == []

    farmer_res = _client(world["farmer_user"]).get("/api/v1/lots/")
    assert [row["id"] for row in farmer_res.data] == [world["lot"].id]

    other = _client(world["other_chief"]).get("/api/v1/lots/")
    assert other.data == []


@pytest.mark.django_db
def test_closed_lot_discloses_bids_to_officers(world):
    submit_bid(lot=world["lot"], buyer=world["buyer"], price_per_kg=1100, terms="cash")
    Lot.objects.filter(pk=world["lot"].id).update(status=LotStatus.CLOSED)
    res = _client(world["chief"]).get("/api/v1/lots/")
    assert [b["price_per_kg"] for b in res.data[0]["bids"]] == [1100]
