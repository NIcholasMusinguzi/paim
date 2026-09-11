from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import Role, ScopeLevel, SystemUser
from apps.analytics.models import DistrictSeasonMetric, NationalSeasonMetric
from apps.farmers.models import Crop, Season
from apps.geo.models import District
from apps.market.models import MarketPrice


@pytest.fixture
def world(db):
    district = District.objects.create(name="Mukono")
    crop = Crop.objects.create(name="Maize")
    today = timezone.localdate()
    season = Season.objects.create(
        year=today.year, season_no=1,
        start_date=today - timedelta(days=10), end_date=today + timedelta(days=100))
    DistrictSeasonMetric.objects.create(
        district=district, season=season, crop=crop, bags_declared=10, pct_grade1=90,
        avg_price_per_kg=1500, parishes_reporting=1, rank_national=1, computed_at=timezone.now())
    NationalSeasonMetric.objects.create(
        season=season, crop=crop, bags_declared=10, pct_grade1=90, avg_price_per_kg=1500,
        districts_reporting=1, computed_at=timezone.now())
    national_admin = SystemUser.objects.create_user(
        phone="+256700000100", password="pin1234", full_name="National Admin",
        role=Role.NATIONAL_ADMIN, scope_level=ScopeLevel.NATIONAL)
    parish_chief = SystemUser.objects.create_user(
        phone="+256700000101", password="pin1234", full_name="Chief",
        role=Role.PARISH_CHIEF, scope_level=ScopeLevel.NATIONAL)
    return {"season": season, "crop": crop, "national_admin": national_admin, "parish_chief": parish_chief}


def _client(user):
    client = APIClient()
    client.post("/api/v1/auth/login/",
                {"phone": user.phone, "password": "pin1234"}, format="json")
    return client


@pytest.mark.django_db
def test_national_metrics_returns_ranked_districts_and_totals(world):
    res = _client(world["national_admin"]).get(
        f"/api/v1/metrics/national/?season={world['season'].id}&crop={world['crop'].id}")
    assert res.status_code == 200
    assert res.data["districts"][0]["district"] == "Mukono"
    assert res.data["national"]["bags_declared"] == 10


@pytest.mark.django_db
def test_national_metrics_requires_season_and_crop(world):
    res = _client(world["national_admin"]).get("/api/v1/metrics/national/")
    assert res.status_code == 400


@pytest.mark.django_db
def test_national_metrics_returns_zero_summary_without_cached_rollup(world):
    NationalSeasonMetric.objects.filter(
        season=world["season"], crop=world["crop"]).delete()
    res = _client(world["national_admin"]).get(
        f"/api/v1/metrics/national/?season={world['season'].id}&crop={world['crop'].id}")
    assert res.status_code == 200
    assert res.data["national"]["farmers_registered"] == 0
    assert res.data["national"]["farmers_active"] == 0
    assert res.data["national"]["avg_price_per_kg"] is None


@pytest.mark.django_db
def test_national_metrics_use_listed_market_price_when_no_awarded_lot(world):
    NationalSeasonMetric.objects.filter(
        season=world["season"], crop=world["crop"]).delete()
    MarketPrice.objects.create(
        item_name="Maize", category="produce", price=1150, unit="UGX/kg",
        market="Katosi", price_date=timezone.localdate(), source="survey")
    res = _client(world["national_admin"]).get(
        f"/api/v1/metrics/national/?season={world['season'].id}&crop={world['crop'].id}")
    assert res.status_code == 200
    assert res.data["national"]["avg_price_per_kg"] == 1150


@pytest.mark.django_db
def test_national_metrics_forbidden_for_parish_chief(world):
    res = _client(world["parish_chief"]).get(
        f"/api/v1/metrics/national/?season={world['season'].id}&crop={world['crop'].id}")
    assert res.status_code == 403
