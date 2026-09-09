import pytest
from rest_framework.test import APIClient

from apps.accounts.models import Role, ScopeLevel, SystemUser
from apps.farmers.models import Farmer
from apps.geo.models import District, Parish, Subcounty, Village


@pytest.fixture
def world(db):
    district = District.objects.create(name="Mukono")
    subcounty = Subcounty.objects.create(district=district, name="Kyampisi")
    parish = Parish.objects.create(subcounty=subcounty, name="Katosi")
    other_parish = Parish.objects.create(subcounty=subcounty, name="Elsewhere")
    village = Village.objects.create(parish=parish, name="Kigunga")

    chief = SystemUser.objects.create_user(
        phone="+256700001100", password="pin1234", full_name="Chief",
        role=Role.PARISH_CHIEF, scope_level=ScopeLevel.PARISH, scope_id=parish.id)
    agent = SystemUser.objects.create_user(
        phone="+256700001101", password="pin1234", full_name="Agent",
        role=Role.AGENT, scope_level=ScopeLevel.PARISH, scope_id=parish.id)
    other_chief = SystemUser.objects.create_user(
        phone="+256700001102", password="pin1234", full_name="Other Chief",
        role=Role.PARISH_CHIEF, scope_level=ScopeLevel.PARISH, scope_id=other_parish.id)
    farmer_user = SystemUser.objects.create_user(
        phone="+256700001103", password="pin1234", full_name="Grace Nabirye",
        role=Role.FARMER, scope_level=ScopeLevel.PARISH, scope_id=parish.id)
    farmer = Farmer.objects.create(village=village, full_name="Grace Nabirye", sex="F",
                                   registered_by=chief, user=farmer_user)

    return {"parish": parish, "chief": chief, "agent": agent, "other_chief": other_chief,
            "farmer_user": farmer_user, "farmer": farmer}


def _client(user):
    client = APIClient()
    client.post("/api/v1/auth/login/",
                {"phone": user.phone, "password": "pin1234"}, format="json")
    return client


@pytest.mark.django_db
def test_farmer_can_submit_a_request(world):
    res = _client(world["farmer_user"]).post(
        "/api/v1/advisory-requests/mine/", {"message": "My maize leaves are yellowing, what should I do?"}, format="json")
    assert res.status_code == 201
    assert res.data["status"] == "open"
    assert res.data["responses"] == []


@pytest.mark.django_db
def test_request_appears_in_the_shared_parish_queue_for_chief_and_agent(world):
    _client(world["farmer_user"]).post(
        "/api/v1/advisory-requests/mine/", {"message": "Help"}, format="json")

    chief_queue = _client(world["chief"]).get(
        "/api/v1/advisory-requests/queue/")
    assert len(chief_queue.data) == 1

    agent_queue = _client(world["agent"]).get(
        "/api/v1/advisory-requests/queue/")
    assert len(agent_queue.data) == 1

    other_queue = _client(world["other_chief"]).get(
        "/api/v1/advisory-requests/queue/")
    assert other_queue.data == []


@pytest.mark.django_db
def test_officer_can_respond_and_farmer_sees_the_response(world):
    created = _client(world["farmer_user"]).post(
        "/api/v1/advisory-requests/mine/", {"message": "Help, yellow leaves"}, format="json")
    request_id = created.data["id"]

    res = _client(world["chief"]).post(
        f"/api/v1/advisory-requests/{request_id}/respond/", {"body": "Sounds like nitrogen deficiency, top-dress with urea."}, format="json")
    assert res.status_code == 200
    assert res.data["status"] == "answered"

    mine = _client(world["farmer_user"]).get("/api/v1/advisory-requests/mine/")
    assert mine.data[0]["responses"][0]["responder_name"] == "Chief"
    assert mine.data[0]["status"] == "answered"


@pytest.mark.django_db
def test_officer_outside_the_parish_cannot_respond(world):
    created = _client(world["farmer_user"]).post(
        "/api/v1/advisory-requests/mine/", {"message": "Help"}, format="json")
    request_id = created.data["id"]

    res = _client(world["other_chief"]).post(
        f"/api/v1/advisory-requests/{request_id}/respond/", {"body": "Not my parish but here's advice"}, format="json")
    assert res.status_code == 403


@pytest.mark.django_db
def test_farmer_cannot_respond_to_their_own_request(world):
    created = _client(world["farmer_user"]).post(
        "/api/v1/advisory-requests/mine/", {"message": "Help"}, format="json")
    request_id = created.data["id"]

    res = _client(world["farmer_user"]).post(
        f"/api/v1/advisory-requests/{request_id}/respond/", {"body": "self-answer"}, format="json")
    assert res.status_code == 403


@pytest.mark.django_db
def test_any_signed_in_user_can_submit_a_request(world):
    res = _client(world["chief"]).post(
        "/api/v1/advisory-requests/mine/", {"message": "x"}, format="json")
    assert res.status_code == 201
    assert res.data["farmer_name"] == "Chief"
