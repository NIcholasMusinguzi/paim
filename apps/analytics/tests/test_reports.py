from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import Role, ScopeLevel, SystemUser
from apps.advisory.models import AdvisoryRequest
from apps.analytics.models import ParishSeasonMetric
from apps.farmers.models import Crop, Farmer, Season
from apps.geo.models import District, Parish, Subcounty, Village
from apps.market.models import Lot


@pytest.fixture
def world(db):
    district = District.objects.create(name="Mukono")
    subcounty = Subcounty.objects.create(district=district, name="Kyampisi")
    parish = Parish.objects.create(subcounty=subcounty, name="Katosi")
    village = Village.objects.create(parish=parish, name="Kigunga")
    crop = Crop.objects.create(name="Maize")
    today = timezone.localdate()
    season = Season.objects.create(
        year=today.year, season_no=1,
        start_date=today - timedelta(days=10), end_date=today + timedelta(days=100))
    chief = SystemUser.objects.create_user(
        phone="+256700000220", password="pin1234", full_name="Chief",
        role=Role.PARISH_CHIEF, scope_level=ScopeLevel.PARISH, scope_id=parish.id)
    farmer = Farmer.objects.create(village=village, full_name="Grace Nabirye", sex="F", registered_by=chief)
    ParishSeasonMetric.objects.create(
        parish=parish, season=season, crop=crop, farmers_registered=12, farmers_active=8,
        bags_declared=40, pct_grade1=70, avg_price_per_kg=1400, computed_at=timezone.now())
    Lot.objects.create(parish=parish, season=season, crop=crop, min_bags=5)
    AdvisoryRequest.objects.create(farmer=farmer, message="Yellowing leaves on maize")
    return {"chief": chief, "season": season, "crop": crop, "district": district}


def _client(user):
    client = APIClient()
    client.post("/api/v1/auth/login/", {"phone": user.phone, "password": "pin1234"}, format="json")
    return client


@pytest.mark.django_db
def test_reports_are_scoped_to_the_viewers_district(world):
    other_district = District.objects.create(name="Wakiso")
    other_sub = Subcounty.objects.create(district=other_district, name="Busukuma")
    other_parish = Parish.objects.create(subcounty=other_sub, name="Nabweru")
    other_village = Village.objects.create(parish=other_parish, name="Other")
    Farmer.objects.create(
        village=other_village, full_name="Outside Farmer", sex="M", registered_by=world["chief"])
    do = SystemUser.objects.create_user(
        phone="+256700000221", password="pin1234", full_name="DO",
        role=Role.DISTRICT_OFFICER, scope_level=ScopeLevel.DISTRICT,
        scope_id=world["district"].id)
    client = _client(do)
    farmers = client.get("/api/v1/reports/farmers/")
    assert farmers.status_code == 200
    names = [row["farmer"] for row in farmers.data]
    assert "Grace Nabirye" in names
    assert "Outside Farmer" not in names

    prices = client.get(
        f"/api/v1/reports/prices/?season={world['season'].id}&crop={world['crop'].id}")
    assert prices.status_code == 200
    assert {row["parish"] for row in prices.data} <= {"Katosi"}

    crops = client.get(f"/api/v1/reports/crops/?season={world['season'].id}")
    assert crops.status_code == 200
    assert crops.data[0]["crop"] == "Maize"


@pytest.mark.django_db
def test_farmers_bids_lots_filter_by_district_within_role(world):
    other_district = District.objects.create(name="Wakiso")
    other_sub = Subcounty.objects.create(district=other_district, name="Busukuma")
    other_parish = Parish.objects.create(subcounty=other_sub, name="Nabweru")
    other_village = Village.objects.create(parish=other_parish, name="Other")
    Farmer.objects.create(
        village=other_village, full_name="Outside Farmer", sex="M", registered_by=world["chief"])
    Lot.objects.create(
        parish=other_parish, season=world["season"], crop=world["crop"], min_bags=5)
    admin = SystemUser.objects.create_user(
        phone="+256700000222", password="pin1234", full_name="NA",
        role=Role.NATIONAL_ADMIN, scope_level=ScopeLevel.NATIONAL)
    client = _client(admin)
    mukono = client.get(f"/api/v1/reports/farmers/?district={world['district'].id}")
    assert [row["farmer"] for row in mukono.data] == ["Grace Nabirye"]
    wakiso = client.get(f"/api/v1/reports/farmers/?district={other_district.id}")
    assert [row["farmer"] for row in wakiso.data] == ["Outside Farmer"]

    lots = client.get(f"/api/v1/reports/lots/?district={world['district'].id}")
    assert {row["parish"] for row in lots.data} == {"Katosi"}

    chief = _client(world["chief"])
    leaked = chief.get(f"/api/v1/reports/farmers/?district={other_district.id}")
    assert leaked.data == []




@pytest.mark.django_db
def test_scoped_json_and_xlsx_export(world):
    client = _client(world["chief"])
    qs = f"?season={world['season'].id}&crop={world['crop'].id}"
    json_res = client.get(f"/api/v1/reports/scoped/{qs}")
    assert json_res.status_code == 200
    assert json_res.data[0]["parish"] == "Katosi"

    xlsx = client.get(f"/api/v1/reports/scoped/{qs}&format=xlsx")
    assert xlsx.status_code == 200
    assert "spreadsheet" in xlsx["Content-Type"]

    pdf = client.get("/api/v1/reports/advisories/?format=pdf")
    assert pdf.status_code == 200
    assert pdf["Content-Type"] == "application/pdf"

    market = client.get(f"/api/v1/reports/market/{qs}")
    assert market.status_code == 200
    assert market.data[0]["crop"] == "Maize"
