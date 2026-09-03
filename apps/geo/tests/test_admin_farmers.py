import pytest
from rest_framework.test import APIClient

from apps.accounts.models import Role, ScopeLevel, SystemUser
from apps.farmers.models import Farmer
from apps.geo.models import District, Parish, Subcounty, Village
from apps.market.models import Declaration, Grade, Lot


@pytest.fixture
def admin(db):
    return SystemUser.objects.create_user(
        phone="+256700000910", password="pin1234", full_name="Admin",
        role=Role.NATIONAL_ADMIN, scope_level=ScopeLevel.NATIONAL)


@pytest.fixture
def village(db):
    district = District.objects.create(name="Mukono")
    subcounty = Subcounty.objects.create(district=district, name="Kyampisi")
    parish = Parish.objects.create(subcounty=subcounty, name="Katosi")
    return Village.objects.create(parish=parish, name="Kigunga")


def _client(user):
    client = APIClient()
    client.post("/api/v1/auth/login/", {"phone": user.phone, "password": "pin1234"}, format="json")
    return client


@pytest.mark.django_db
def test_admin_can_create_a_farmer_and_is_recorded_as_registering_it(admin, village):
    client = _client(admin)
    res = client.post("/api/v1/admin/farmers/", {
        "full_name": "Grace Nabirye", "sex": "F", "village": village.id,
        "phone": "+256701111222", "language": "lug", "reach_channel": "agent",
    }, format="json")
    assert res.status_code == 201
    assert res.data["village_name"] == "Kigunga"
    assert res.data["parish_name"] == "Katosi"
    assert res.data["district_name"] == "Mukono"
    assert res.data["registered_by_name"] == "Admin"

    farmer = Farmer.objects.get(full_name="Grace Nabirye")
    assert farmer.registered_by == admin


@pytest.mark.django_db
def test_admin_can_edit_and_list_farmers(admin, village):
    client = _client(admin)
    create = client.post("/api/v1/admin/farmers/", {
        "full_name": "Grace Nabirye", "sex": "F", "village": village.id,
    }, format="json")
    farmer_id = create.data["id"]

    update = client.patch(f"/api/v1/admin/farmers/{farmer_id}/", {"phone": "+256709998888"}, format="json")
    assert update.status_code == 200
    assert update.data["phone"] == "+256709998888"

    listing = client.get("/api/v1/admin/farmers/")
    assert any(f["id"] == farmer_id for f in listing.data)


@pytest.mark.django_db
def test_deleting_a_farmer_with_declarations_returns_409(admin, village):
    from datetime import timedelta

    from django.utils import timezone

    from apps.farmers.models import Crop, Season

    client = _client(admin)
    farmer = Farmer.objects.create(village=village, full_name="Grace Nabirye", sex="F", registered_by=admin)
    crop = Crop.objects.create(name="Maize")
    today = timezone.localdate()
    season = Season.objects.create(
        year=today.year, season_no=1,
        start_date=today - timedelta(days=5), end_date=today + timedelta(days=100))
    lot = Lot.objects.create(parish=village.parish, season=season, crop=crop, min_bags=10)
    Declaration.objects.create(farmer=farmer, lot=lot, bags=3, grade=Grade.UNGRADED, declared_via="agent")

    res = client.delete(f"/api/v1/admin/farmers/{farmer.id}/")
    assert res.status_code == 409
    assert Farmer.objects.filter(id=farmer.id).exists()


@pytest.mark.django_db
def test_non_admin_cannot_manage_farmers(village):
    chief = SystemUser.objects.create_user(
        phone="+256700000911", password="pin1234", full_name="Chief",
        role=Role.PARISH_CHIEF, scope_level=ScopeLevel.PARISH, scope_id=village.parish_id)
    res = _client(chief).get("/api/v1/admin/farmers/")
    assert res.status_code == 403
