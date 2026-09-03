import pytest
from rest_framework.test import APIClient

from apps.accounts.models import Role, ScopeLevel, SystemUser
from apps.geo.models import District, Parish, Subcounty, Village


@pytest.fixture
def admin(db):
    return SystemUser.objects.create_user(
        phone="+256700000900", password="pin1234", full_name="Admin",
        role=Role.NATIONAL_ADMIN, scope_level=ScopeLevel.NATIONAL)


@pytest.fixture
def chief(db):
    district = District.objects.create(name="Mukono")
    subcounty = Subcounty.objects.create(district=district, name="Kyampisi")
    parish = Parish.objects.create(subcounty=subcounty, name="Katosi")
    return SystemUser.objects.create_user(
        phone="+256700000901", password="pin1234", full_name="Chief",
        role=Role.PARISH_CHIEF, scope_level=ScopeLevel.PARISH, scope_id=parish.id)


def _client(user):
    client = APIClient()
    client.post("/api/v1/auth/login/", {"phone": user.phone, "password": "pin1234"}, format="json")
    return client


@pytest.mark.django_db
def test_non_admin_cannot_reach_the_admin_api(chief):
    res = _client(chief).get("/api/v1/admin/districts/")
    assert res.status_code == 403


@pytest.mark.django_db
def test_admin_can_crud_a_district(admin):
    client = _client(admin)
    create = client.post("/api/v1/admin/districts/", {"name": "Kayunga", "region": "Central"}, format="json")
    assert create.status_code == 201
    district_id = create.data["id"]

    listing = client.get("/api/v1/admin/districts/")
    assert any(d["name"] == "Kayunga" for d in listing.data)

    update = client.patch(f"/api/v1/admin/districts/{district_id}/", {"region": "Eastern"}, format="json")
    assert update.status_code == 200
    assert update.data["region"] == "Eastern"

    delete = client.delete(f"/api/v1/admin/districts/{district_id}/")
    assert delete.status_code == 204
    assert not District.objects.filter(id=district_id).exists()


@pytest.mark.django_db
def test_deleting_a_referenced_district_returns_409_not_500(admin):
    district = District.objects.create(name="Mukono")
    Subcounty.objects.create(district=district, name="Kyampisi")
    res = _client(admin).delete(f"/api/v1/admin/districts/{district.id}/")
    assert res.status_code == 409
    assert District.objects.filter(id=district.id).exists()


@pytest.mark.django_db
def test_full_geography_hierarchy_shows_readable_names(admin):
    district = District.objects.create(name="Mukono")
    subcounty = Subcounty.objects.create(district=district, name="Kyampisi")
    parish = Parish.objects.create(subcounty=subcounty, name="Katosi")
    Village.objects.create(parish=parish, name="Kigunga")

    client = _client(admin)
    res = client.get("/api/v1/admin/villages/")
    assert res.data[0]["parish_name"] == "Katosi"

    res = client.get("/api/v1/admin/parishes/")
    assert res.data[0]["district_name"] == "Mukono"


@pytest.mark.django_db
def test_create_user_requires_password_and_valid_scope(admin):
    district = District.objects.create(name="Mukono")
    client = _client(admin)

    no_password = client.post("/api/v1/admin/users/", {
        "phone": "+256700000902", "full_name": "New Officer",
        "role": Role.DISTRICT_OFFICER, "scope_level": ScopeLevel.DISTRICT, "scope_id": district.id,
    }, format="json")
    assert no_password.status_code == 400

    bad_scope = client.post("/api/v1/admin/users/", {
        "phone": "+256700000902", "password": "pin1234", "full_name": "New Officer",
        "role": Role.DISTRICT_OFFICER, "scope_level": ScopeLevel.NATIONAL, "scope_id": district.id,
    }, format="json")
    assert bad_scope.status_code == 400

    ok = client.post("/api/v1/admin/users/", {
        "phone": "+256700000902", "password": "pin1234", "full_name": "New Officer",
        "role": Role.DISTRICT_OFFICER, "scope_level": ScopeLevel.DISTRICT, "scope_id": district.id,
    }, format="json")
    assert ok.status_code == 201
    assert "password" not in ok.data

    new_user = SystemUser.objects.get(phone="+256700000902")
    assert new_user.check_password("pin1234")


@pytest.mark.django_db
def test_deactivating_a_user_does_not_delete_them(admin, chief):
    client = _client(admin)
    res = client.patch(f"/api/v1/admin/users/{chief.id}/", {"is_active": False}, format="json")
    assert res.status_code == 200
    chief.refresh_from_db()
    assert chief.is_active is False

    assert client.delete(f"/api/v1/admin/users/{chief.id}/").status_code == 405


@pytest.mark.django_db
def test_buyer_must_link_to_a_buyer_role_account(admin, chief):
    res = _client(admin).post("/api/v1/admin/buyers/", {
        "name": "Nile Grain Traders", "licence_no": "LIC-900", "user": chief.id,
    }, format="json")
    assert res.status_code == 400
