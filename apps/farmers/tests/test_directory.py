import pytest
from rest_framework.test import APIClient

from datetime import timedelta

from django.utils import timezone

from apps.accounts.models import Role, ScopeLevel, SystemUser
from apps.farmers.models import Crop, Farmer, Planting, Plot, Season
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
    maize = Crop.objects.create(name="Maize")
    beans = Crop.objects.create(name="Beans")
    today = timezone.localdate()
    season = Season.objects.create(
        year=today.year, season_no=1,
        start_date=today - timedelta(days=10), end_date=today + timedelta(days=100))
    plot = Plot.objects.create(farmer=grace, area_acres="1.00")
    Planting.objects.create(plot=plot, season=season, crop=maize, planting_date=today)
    Planting.objects.create(plot=plot, season=season, crop=beans, planting_date=today)
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


@pytest.mark.django_db
def test_directory_includes_crops_the_farmer_grows(world):
    rows = {row["full_name"]: row for row in _client(world["admin"]).get("/api/v1/farmers/").data}
    assert set(rows["Grace Nabirye"]["crops"]) == {"Maize", "Beans"}
    assert rows["Kato Peter"]["crops"] == []
