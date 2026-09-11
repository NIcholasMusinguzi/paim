from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import Role, ScopeLevel, SystemUser
from apps.analytics.models import DistrictSeasonMetric, ParishSeasonMetric
from apps.farmers.models import Crop, Season
from apps.geo.models import District, Parish, Subcounty, Village
from apps.market.models import Lot


def _client(user):
    client = APIClient()
    client.post("/api/v1/auth/login/", {"phone": user.phone, "password": "pin1234"}, format="json")
    return client


@pytest.fixture
def world(db):
    mukono = District.objects.create(name="Mukono")
    wakiso = District.objects.create(name="Wakiso")
    kyampisi = Subcounty.objects.create(district=mukono, name="Kyampisi")
    nabweru = Subcounty.objects.create(district=wakiso, name="Nabweru")
    katosi = Parish.objects.create(subcounty=kyampisi, name="Katosi")
    nagojie = Parish.objects.create(subcounty=kyampisi, name="Nagojie")
    nabweru_parish = Parish.objects.create(subcounty=nabweru, name="Nabweru")
    Village.objects.create(parish=katosi, name="Kigunga")
    crop = Crop.objects.create(name="Maize")
    today = timezone.localdate()
    past = Season.objects.create(
        year=today.year - 1, season_no=2,
        start_date=today - timedelta(days=400), end_date=today - timedelta(days=250))
    current = Season.objects.create(
        year=today.year, season_no=1,
        start_date=today - timedelta(days=30), end_date=today + timedelta(days=90))
    now = timezone.now()
    ParishSeasonMetric.objects.create(
        parish=katosi, season=current, crop=crop, farmers_registered=10, farmers_active=7,
        bags_declared=80, pct_grade1=85, avg_price_per_kg=1140, computed_at=now)
    ParishSeasonMetric.objects.create(
        parish=nagojie, season=current, crop=crop, farmers_registered=20, farmers_active=10,
        bags_declared=40, pct_grade1=44, avg_price_per_kg=955, computed_at=now)
    DistrictSeasonMetric.objects.create(
        district=mukono, season=past, crop=crop, bags_declared=50, pct_grade1=38,
        avg_price_per_kg=880, parishes_reporting=2, computed_at=now)
    DistrictSeasonMetric.objects.create(
        district=mukono, season=current, crop=crop, bags_declared=120, pct_grade1=70,
        avg_price_per_kg=1100, parishes_reporting=2, computed_at=now)
    Lot.objects.create(parish=katosi, season=current, crop=crop, min_bags=15, status="open")
    chief = SystemUser.objects.create_user(
        phone="+256700000301", password="pin1234", full_name="Chief",
        role=Role.PARISH_CHIEF, scope_level=ScopeLevel.PARISH, scope_id=katosi.id)
    admin = SystemUser.objects.create_user(
        phone="+256700000302", password="pin1234", full_name="Admin",
        role=Role.NATIONAL_ADMIN, scope_level=ScopeLevel.NATIONAL)
    return {
        "mukono": mukono, "wakiso": wakiso, "katosi": katosi, "crop": crop,
        "current": current, "chief": chief, "admin": admin,
    }


@pytest.mark.django_db
def test_admin_parish_comparison_includes_live_and_agent_reach(world):
    res = _client(world["admin"]).get(
        f"/api/v1/metrics/district/{world['mukono'].id}/parishes/"
        f"?season={world['current'].id}&crop={world['crop'].id}")
    assert res.status_code == 200
    by_name = {row["parish"]: row for row in res.data}
    assert by_name["Katosi"]["live"] is True
    assert by_name["Katosi"]["agent_reach"] == 70
    assert by_name["Nagojie"]["live"] is False
    assert by_name["Katosi"]["pct_grade1"] == 85


@pytest.mark.django_db
def test_parish_chief_does_not_see_other_districts(world):
    own = _client(world["chief"]).get(
        f"/api/v1/metrics/district/{world['mukono'].id}/parishes/"
        f"?season={world['current'].id}&crop={world['crop'].id}")
    assert {row["parish"] for row in own.data} == {"Katosi"}
    other = _client(world["chief"]).get(
        f"/api/v1/metrics/district/{world['wakiso'].id}/parishes/"
        f"?season={world['current'].id}&crop={world['crop'].id}")
    assert other.status_code == 403


@pytest.mark.django_db
def test_district_season_bars_are_chronological(world):
    res = _client(world["admin"]).get(
        f"/api/v1/metrics/district/{world['mukono'].id}/seasons/?crop={world['crop'].id}")
    assert res.status_code == 200
    assert [row["pct_grade1"] for row in res.data] == [38, 70]
    assert res.data[0]["label"].endswith("B")
    assert res.data[1]["label"].endswith("A")
