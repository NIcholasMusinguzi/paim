from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import Role, ScopeLevel, SystemUser
from apps.advisory.models import AdvisoryContent
from apps.analytics.models import ParishSeasonMetric, TrendInsight
from apps.farmers.models import Crop, Farmer, Planting, Plot, Season
from apps.geo.models import District, Parish, Subcounty, Village
from apps.market.models import Declaration, Grade, Lot


@pytest.fixture
def world(db):
    district = District.objects.create(name="Mukono")
    subcounty = Subcounty.objects.create(district=district, name="Kyampisi")
    parish = Parish.objects.create(subcounty=subcounty, name="Katosi", lot_min_bags=10)
    village = Village.objects.create(parish=parish, name="Kigunga")
    crop = Crop.objects.create(name="Maize")
    today = timezone.localdate()
    season = Season.objects.create(
        year=today.year, season_no=1,
        start_date=today - timedelta(days=30), end_date=today + timedelta(days=90))

    agent = SystemUser.objects.create_user(
        phone="+256700000030", full_name="Agent", role=Role.AGENT,
        scope_level=ScopeLevel.PARISH, scope_id=parish.id)
    farmer_user = SystemUser.objects.create_user(
        phone="+256700000031", password="pin1234", full_name="Grace Nabirye",
        role=Role.FARMER, scope_level=ScopeLevel.PARISH, scope_id=parish.id)
    farmer = Farmer.objects.create(
        village=village, full_name="Grace Nabirye", sex="F",
        registered_by=agent, user=farmer_user, language="en")
    plot = Plot.objects.create(farmer=farmer, area_acres="1.5")
    Planting.objects.create(plot=plot, season=season, crop=crop, planting_date=today - timedelta(weeks=3))

    AdvisoryContent.objects.create(
        crop=crop, agro_zone="", week_from=0, week_to=6, language="en",
        body="Weed now to protect yield.", source="MAAIF", status="validated")

    lot = Lot.objects.create(parish=parish, season=season, crop=crop, min_bags=10)
    Declaration.objects.create(farmer=farmer, lot=lot, bags=5, grade=Grade.G1, declared_via="web")

    ParishSeasonMetric.objects.create(
        parish=parish, season=season, crop=crop, avg_price_per_kg=1200, computed_at=timezone.now())

    TrendInsight.objects.create(
        scope_level=ScopeLevel.PARISH, scope_id=parish.id, crop=crop, metric="avg_price_per_kg",
        direction="up", magnitude="5.00", window_weeks=3, message="Prices are rising in Katosi.",
        published_at=timezone.now())
    TrendInsight.objects.create(
        scope_level=ScopeLevel.DISTRICT, scope_id=district.id, crop=crop, metric="avg_price_per_kg",
        direction="up", magnitude="3.00", window_weeks=3, message="Prices rising across Mukono.",
        published_at=timezone.now())
    TrendInsight.objects.create(
        scope_level=ScopeLevel.PARISH, scope_id=parish.id, crop=crop, metric="pct_grade1",
        direction="down", magnitude="2.00", window_weeks=3, message="Draft, not yet approved.",
        published_at=None)

    return {"farmer": farmer, "parish": parish, "crop": crop}


@pytest.mark.django_db
def test_farmer_home_composes_advice_lot_price_and_trends(world):
    client = APIClient()
    client.post("/api/v1/auth/login/", {"phone": "+256700000031", "password": "pin1234"}, format="json")
    res = client.get("/api/v1/farmer/home/")
    assert res.status_code == 200
    body = res.data

    assert body["farmer"]["full_name"] == "Grace Nabirye"
    assert [a["body"] for a in body["advice"]] == ["Weed now to protect yield."]

    assert len(body["lots"]) == 1
    assert body["lots"][0]["crop"] == "Maize"
    assert body["lots"][0]["bags"] == 5

    assert body["prices"] == [{"crop": "Maize", "avg_price_per_kg": 1200,
                                "computed_at": body["prices"][0]["computed_at"]}]

    assert len(body["declarations"]) == 1
    assert body["declarations"][0]["bags"] == 5

    messages = {t["message"] for t in body["trends"]}
    assert messages == {"Prices are rising in Katosi.", "Prices rising across Mukono."}
    assert "Draft, not yet approved." not in messages


@pytest.mark.django_db
def test_farmer_home_rejects_non_farmer_roles(world):
    officer = SystemUser.objects.create_user(
        phone="+256700000032", password="pin1234", full_name="Chief",
        role=Role.PARISH_CHIEF, scope_level=ScopeLevel.PARISH, scope_id=world["parish"].id)
    client = APIClient()
    client.post("/api/v1/auth/login/", {"phone": officer.phone, "password": "pin1234"}, format="json")
    assert client.get("/api/v1/farmer/home/").status_code == 403


@pytest.mark.django_db
def test_farmer_home_404s_without_a_linked_profile(db):
    user = SystemUser.objects.create_user(
        phone="+256700000033", password="pin1234", full_name="No Profile",
        role=Role.FARMER, scope_level=ScopeLevel.NATIONAL)
    client = APIClient()
    client.post("/api/v1/auth/login/", {"phone": user.phone, "password": "pin1234"}, format="json")
    assert client.get("/api/v1/farmer/home/").status_code == 404


@pytest.mark.django_db
def test_reference_data_lists_seasons_and_crops(world):
    client = APIClient()
    client.post("/api/v1/auth/login/", {"phone": "+256700000031", "password": "pin1234"}, format="json")
    res = client.get("/api/v1/reference/")
    assert res.status_code == 200
    assert [c["name"] for c in res.data["crops"]] == ["Maize"]
    assert len(res.data["seasons"]) == 1


@pytest.mark.django_db
def test_farmer_profile_can_grow_multiple_crops(world):
    beans = Crop.objects.create(name="Beans")
    client = APIClient()
    client.post("/api/v1/auth/login/", {"phone": "+256700000031", "password": "pin1234"}, format="json")
    maize_id = world["crop"].id
    res = client.patch("/api/v1/farmer/profile/", {
        "crop_ids": [maize_id, beans.id],
    }, format="json")
    assert res.status_code == 200
    assert set(res.data["crop_ids"]) == {maize_id, beans.id}
    assert set(res.data["crops"]) == {"Maize", "Beans"}
    assert Planting.objects.filter(plot__farmer=world["farmer"]).count() == 2
