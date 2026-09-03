from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import Role, ScopeLevel, SystemUser
from apps.analytics.models import ParishSeasonMetric
from apps.farmers.models import Crop, Farmer, Season
from apps.geo.models import District, Parish, Subcounty, Village
from apps.market.models import Declaration, Grade, Lot


@pytest.fixture
def world(db):
    district = District.objects.create(name="Mukono")
    subcounty = Subcounty.objects.create(district=district, name="Kyampisi")
    parish = Parish.objects.create(subcounty=subcounty, name="Katosi", lot_min_bags=10)
    other_parish = Parish.objects.create(subcounty=subcounty, name="Elsewhere")
    village = Village.objects.create(parish=parish, name="Kigunga")
    crop = Crop.objects.create(name="Maize")
    today = timezone.localdate()
    season = Season.objects.create(
        year=today.year, season_no=1,
        start_date=today - timedelta(days=10), end_date=today + timedelta(days=100))
    chief = SystemUser.objects.create_user(
        phone="+256700000060", password="pin1234", full_name="Chief",
        role=Role.PARISH_CHIEF, scope_level=ScopeLevel.PARISH, scope_id=parish.id)
    farmer = Farmer.objects.create(village=village, full_name="Grace Nabirye", sex="F", registered_by=chief)
    lot = Lot.objects.create(parish=parish, season=season, crop=crop, min_bags=10)
    Declaration.objects.create(farmer=farmer, lot=lot, bags=4, grade=Grade.G1, declared_via="web")
    ParishSeasonMetric.objects.create(
        parish=parish, season=season, crop=crop, bags_declared=4, pct_grade1=100,
        farmers_active=1, avg_price_per_kg=1200, computed_at=timezone.now())
    return {"parish": parish, "other_parish": other_parish, "chief": chief, "lot": lot}


def _client(user):
    client = APIClient()
    client.post("/api/v1/auth/login/", {"phone": user.phone, "password": "pin1234"}, format="json")
    return client


@pytest.mark.django_db
def test_dashboard_composes_parish_lot_declarations_and_metrics(world):
    res = _client(world["chief"]).get(f"/api/v1/parish/{world['parish'].id}/dashboard/")
    assert res.status_code == 200
    assert res.data["parish"]["name"] == "Katosi"
    assert res.data["lot"]["crop"] == "Maize"
    assert res.data["lot"]["bags"] == 4
    assert len(res.data["declarations"]) == 1
    assert res.data["declarations"][0]["farmer_name"] == "Grace Nabirye"
    assert res.data["metrics"]["pct_grade1"] == 100


@pytest.mark.django_db
def test_dashboard_rejects_out_of_scope_parish(world):
    res = _client(world["chief"]).get(f"/api/v1/parish/{world['other_parish'].id}/dashboard/")
    assert res.status_code == 403


@pytest.mark.django_db
def test_parish_list_is_scoped(world):
    res = _client(world["chief"]).get("/api/v1/parishes/")
    assert [p["name"] for p in res.data] == ["Katosi"]


@pytest.mark.django_db
def test_dashboard_rejects_a_farmer_even_for_their_own_parish(world):
    # A farmer's account also carries scope_level=parish/scope_id=their
    # parish (needed for /farmer/home/), so parish_ids_for() alone would
    # let them in — the role matrix reserves this view for officers.
    farmer_user = SystemUser.objects.create_user(
        phone="+256700000061", password="pin1234", full_name="Grace Nabirye",
        role=Role.FARMER, scope_level=ScopeLevel.PARISH, scope_id=world["parish"].id)
    res = _client(farmer_user).get(f"/api/v1/parish/{world['parish'].id}/dashboard/")
    assert res.status_code == 403
