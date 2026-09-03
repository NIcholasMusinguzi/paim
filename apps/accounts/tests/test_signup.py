import pytest
from rest_framework.test import APIClient

from apps.accounts.models import Role
from apps.farmers.models import Farmer
from apps.geo.models import District, Parish, Subcounty, Village


@pytest.fixture
def village(db):
    district = District.objects.create(name="Mukono")
    subcounty = Subcounty.objects.create(district=district, name="Kyampisi")
    parish = Parish.objects.create(subcounty=subcounty, name="Katosi")
    return Village.objects.create(parish=parish, name="Kigunga")


@pytest.mark.django_db
def test_public_villages_endpoint_needs_no_auth(village):
    res = APIClient().get("/api/v1/villages/")
    assert res.status_code == 200
    assert res.data == [{"id": village.id, "name": "Kigunga", "parish": "Katosi", "district": "Mukono"}]


@pytest.mark.django_db
def test_signup_creates_account_and_farmer_and_signs_in(village):
    client = APIClient()
    res = client.post("/api/v1/auth/signup/", {
        "phone": "+256701234567", "password": "pin1234", "full_name": "Grace Nabirye",
        "sex": "F", "village_id": village.id,
    }, format="json")
    assert res.status_code == 200
    assert res.data["role"] == Role.FARMER

    farmer = Farmer.objects.get(phone="+256701234567")
    assert farmer.full_name == "Grace Nabirye"
    assert farmer.registered_by is None
    assert farmer.user.phone == "+256701234567"

    # The signup response set auth cookies, so the farmer is signed in immediately.
    me = client.get("/api/v1/me/")
    assert me.status_code == 200
    assert me.data["full_name"] == "Grace Nabirye"


@pytest.mark.django_db
def test_signup_links_to_an_existing_agent_registered_profile(village):
    from apps.accounts.models import ScopeLevel, SystemUser

    agent = SystemUser.objects.create_user(
        phone="+256700000200", full_name="Agent", role=Role.AGENT,
        scope_level=ScopeLevel.PARISH, scope_id=village.parish_id)
    existing = Farmer.objects.create(
        village=village, full_name="Grace Nabirye", sex="F", phone="+256701234567", registered_by=agent)

    client = APIClient()
    res = client.post("/api/v1/auth/signup/", {
        "phone": "+256701234567", "password": "pin1234", "full_name": "Grace Nabirye",
        "sex": "F", "village_id": village.id,
    }, format="json")
    assert res.status_code == 200
    assert Farmer.objects.count() == 1
    existing.refresh_from_db()
    assert existing.user.phone == "+256701234567"


@pytest.mark.django_db
def test_signup_rejects_a_phone_already_in_use(village):
    client = APIClient()
    client.post("/api/v1/auth/signup/", {
        "phone": "+256701234567", "password": "pin1234", "full_name": "Grace Nabirye",
        "sex": "F", "village_id": village.id,
    }, format="json")
    res = client.post("/api/v1/auth/signup/", {
        "phone": "+256701234567", "password": "other1234", "full_name": "Someone Else",
        "sex": "M", "village_id": village.id,
    }, format="json")
    assert res.status_code == 409


@pytest.mark.django_db
def test_signup_rejects_an_invalid_village(village):
    res = APIClient().post("/api/v1/auth/signup/", {
        "phone": "+256701234567", "password": "pin1234", "full_name": "Grace Nabirye",
        "sex": "F", "village_id": village.id + 999,
    }, format="json")
    assert res.status_code == 400
