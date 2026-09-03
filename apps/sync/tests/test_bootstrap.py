from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import Role, ScopeLevel, SystemUser
from apps.farmers.models import Crop, Farmer, Season
from apps.geo.models import District, Parish, Subcounty, Village
from apps.market.models import Declaration, Grade, Lot


@pytest.mark.django_db
def test_bootstrap_returns_parish_reference_data_and_open_lots():
    district = District.objects.create(name="Mukono")
    subcounty = Subcounty.objects.create(district=district, name="Kyampisi")
    parish = Parish.objects.create(subcounty=subcounty, name="Katosi", lot_min_bags=10)
    village = Village.objects.create(parish=parish, name="Kigunga")
    crop = Crop.objects.create(name="Maize")
    today = timezone.localdate()
    season = Season.objects.create(
        year=today.year, season_no=1,
        start_date=today - timedelta(days=10), end_date=today + timedelta(days=100))

    agent = SystemUser.objects.create_user(
        phone="+256700000050", password="pin1234", full_name="Agent",
        role=Role.AGENT, scope_level=ScopeLevel.PARISH, scope_id=parish.id)
    farmer = Farmer.objects.create(village=village, full_name="Grace Nabirye", sex="F", registered_by=agent)
    lot = Lot.objects.create(parish=parish, season=season, crop=crop, min_bags=10)
    Declaration.objects.create(farmer=farmer, lot=lot, bags=4, grade=Grade.G1, declared_via="web")

    client = APIClient()
    client.post("/api/v1/auth/login/", {"phone": agent.phone, "password": "pin1234"}, format="json")
    res = client.get("/api/v1/sync/bootstrap/")

    assert res.status_code == 200
    assert res.data["parish_id"] == parish.id
    assert [v["name"] for v in res.data["villages"]] == ["Kigunga"]
    assert [c["name"] for c in res.data["crops"]] == ["Maize"]
    assert [f["full_name"] for f in res.data["farmers"]] == ["Grace Nabirye"]
    assert res.data["open_lots"] == [
        {"id": lot.id, "crop_id": crop.id, "crop": "Maize", "bags": 4, "min_bags": 10}
    ]


@pytest.mark.django_db
def test_bootstrap_rejects_non_agents():
    user = SystemUser.objects.create_user(
        phone="+256700000051", password="pin1234", full_name="Chief",
        role=Role.PARISH_CHIEF, scope_level=ScopeLevel.NATIONAL)
    client = APIClient()
    client.post("/api/v1/auth/login/", {"phone": user.phone, "password": "pin1234"}, format="json")
    assert client.get("/api/v1/sync/bootstrap/").status_code == 403
