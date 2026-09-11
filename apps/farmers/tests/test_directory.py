import pytest
from rest_framework.test import APIClient

from apps.accounts.models import Role, ScopeLevel, SystemUser
from apps.farmers.models import Farmer
from apps.geo.models import District, Parish, Subcounty, Village


def _client(user, password="pin1234"):
    client = APIClient()
    client.post("/api/v1/auth/login/", {"phone": user.phone, "password": password}, format="json")
    return client


@pytest.fixture
def world(db):
    mukono = District.objects.create(name="Mukono")
    kyampisi = Subcounty.objects.create(district=mukono, name="Kyampisi")
    katosi = Parish.objects.create(subcounty=kyampisi, name="Katosi")
    nama = Parish.objects.create(subcounty=kyampisi, name="Nama")
    kigunga = Village.objects.create(parish=katosi, name="Kigunga")
    nakabago = Village.objects.create(parish=nama, name="Nakabago")
    grace = Farmer.objects.create(village=kigunga, full_name="Grace Nabirye", sex="F")
    peter = Farmer.objects.create(village=nakabago, full_name="Kato Peter", sex="M")
    chief = SystemUser.objects.create_user(
        phone="+256700000201", password="pin1234", full_name="Katosi Chief",
        role=Role.PARISH_CHIEF, scope_level=ScopeLevel.PARISH, scope_id=katosi.id)
    subcounty = SystemUser.objects.create_user(
        phone="+256700000202", password="pin1234", full_name="Kyampisi Officer",
        role=Role.SUBCOUNTY_OFFICER, scope_level=ScopeLevel.SUBCOUNTY, scope_id=kyampisi.id)
    admin = SystemUser.objects.create_user(
        phone="+256700000203", password="pin1234", full_name="Admin",
        role=Role.NATIONAL_ADMIN, scope_level=ScopeLevel.NATIONAL)
    return {
        "grace": grace, "peter": peter, "chief": chief, "subcounty": subcounty, "admin": admin,
    }


@pytest.mark.django_db
def test_parish_chief_sees_only_own_parish_farmers(world):
    names = {row["full_name"] for row in _client(world["chief"]).get("/api/v1/farmers/").data}
    assert names == {"Grace Nabirye"}


@pytest.mark.django_db
def test_subcounty_officer_and_admin_see_farmers_in_scope(world):
    subcounty_names = {row["full_name"] for row in _client(world["subcounty"]).get("/api/v1/farmers/").data}
    admin_names = {row["full_name"] for row in _client(world["admin"]).get("/api/v1/farmers/").data}
    assert subcounty_names == {"Grace Nabirye", "Kato Peter"}
    assert admin_names == {"Grace Nabirye", "Kato Peter"}
