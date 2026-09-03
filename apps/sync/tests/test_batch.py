from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import Role, ScopeLevel, SystemUser
from apps.farmers.models import Crop, Farmer, Season
from apps.geo.models import District, Parish, Subcounty, Village
from apps.market.models import Lot


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
        start_date=today - timedelta(days=10), end_date=today + timedelta(days=100))
    agent = SystemUser.objects.create_user(
        phone="+256700000040", password="pin1234", full_name="Agent",
        role=Role.AGENT, scope_level=ScopeLevel.PARISH, scope_id=parish.id)
    return {"parish": parish, "village": village, "crop": crop, "season": season, "agent": agent}


def _client(agent):
    client = APIClient()
    client.post("/api/v1/auth/login/", {"phone": agent.phone, "password": "pin1234"}, format="json")
    return client


@pytest.mark.django_db
def test_farmer_create_and_declaration_create_apply(world):
    client = _client(world["agent"])
    body = {
        "device_id": "device-1",
        "operations": [
            {"op_id": "op-1", "type": "farmer.create", "at": timezone.now().isoformat(),
             "payload": {"full_name": "Grace Nabirye", "village_id": world["village"].id, "sex": "F"}},
        ],
    }
    res = client.post("/api/v1/sync/batch/", body, format="json")
    assert res.status_code == 200
    assert res.data["results"][0]["status"] == "applied"
    farmer_id = res.data["results"][0]["farmer_id"]
    assert Farmer.objects.filter(pk=farmer_id).exists()

    body2 = {
        "device_id": "device-1",
        "operations": [
            {"op_id": "op-2", "type": "declaration.create", "at": timezone.now().isoformat(),
             "payload": {"farmer_id": farmer_id, "crop_id": world["crop"].id, "bags": 5}},
        ],
    }
    res2 = client.post("/api/v1/sync/batch/", body2, format="json")
    assert res2.data["results"][0]["status"] == "applied"
    assert res2.data["results"][0]["grade"] == "ungraded"


@pytest.mark.django_db
def test_replaying_a_batch_is_a_no_op(world):
    client = _client(world["agent"])
    body = {
        "device_id": "device-1",
        "operations": [
            {"op_id": "op-dup", "type": "farmer.create", "at": timezone.now().isoformat(),
             "payload": {"full_name": "Grace Nabirye", "village_id": world["village"].id, "sex": "F"}},
        ],
    }
    first = client.post("/api/v1/sync/batch/", body, format="json")
    second = client.post("/api/v1/sync/batch/", body, format="json")
    assert first.data["results"][0]["farmer_id"] == second.data["results"][0]["farmer_id"]
    assert Farmer.objects.filter(full_name="Grace Nabirye").count() == 1


@pytest.mark.django_db
def test_farmer_created_offline_twice_does_not_duplicate(world):
    client = _client(world["agent"])
    payload = {"full_name": "Grace Nabirye", "village_id": world["village"].id, "sex": "F", "phone": "+256711000001"}
    res1 = client.post("/api/v1/sync/batch/", {
        "device_id": "device-1",
        "operations": [{"op_id": "op-a", "type": "farmer.create", "at": timezone.now().isoformat(), "payload": payload}],
    }, format="json")
    res2 = client.post("/api/v1/sync/batch/", {
        "device_id": "device-1",
        "operations": [{"op_id": "op-b", "type": "farmer.create", "at": timezone.now().isoformat(), "payload": payload}],
    }, format="json")
    assert res1.data["results"][0]["farmer_id"] == res2.data["results"][0]["farmer_id"]
    assert res2.data["results"][0]["created"] is False
    assert Farmer.objects.filter(full_name="Grace Nabirye").count() == 1


@pytest.mark.django_db
def test_declaration_after_lot_closed_is_rejected(world):
    client = _client(world["agent"])
    farmer = Farmer.objects.create(village=world["village"], full_name="Late Farmer", sex="F",
                                   registered_by=world["agent"])
    lot = Lot.objects.create(parish=world["parish"], season=world["season"], crop=world["crop"], min_bags=1)
    lot.status = "closed"
    lot.save(update_fields=["status"])

    res = client.post("/api/v1/sync/batch/", {
        "device_id": "device-1",
        "operations": [{"op_id": "op-late", "type": "declaration.create", "at": timezone.now().isoformat(),
                        "payload": {"farmer_id": farmer.id, "crop_id": world["crop"].id, "bags": 3}}],
    }, format="json")
    assert res.data["results"][0]["status"] == "rejected"
    assert res.data["results"][0]["reason"] == "lot_closed"


@pytest.mark.django_db
def test_non_agent_cannot_post_batches(world):
    farmer_user = SystemUser.objects.create_user(
        phone="+256700000041", password="pin1234", full_name="Farmer",
        role=Role.FARMER, scope_level=ScopeLevel.PARISH, scope_id=world["parish"].id)
    client = _client(farmer_user)
    res = client.post("/api/v1/sync/batch/", {"device_id": "d", "operations": []}, format="json")
    assert res.status_code == 403
