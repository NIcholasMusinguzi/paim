import pytest
from rest_framework.test import APIClient

from apps.accounts.models import Role, ScopeLevel, SystemUser
from apps.advisory.models import AdvisoryDelivery
from apps.analytics.models import TrendInsight
from apps.analytics.trends import TrendApprovalError, approve_insight
from apps.farmers.models import Crop, Farmer
from apps.geo.models import District, Parish, Subcounty, Village


@pytest.fixture
def world(db):
    district = District.objects.create(name="Mukono")
    subcounty = Subcounty.objects.create(district=district, name="Kyampisi")
    parish = Parish.objects.create(subcounty=subcounty, name="Katosi")
    other_district = District.objects.create(name="Wakiso")
    village = Village.objects.create(parish=parish, name="Kigunga")
    crop = Crop.objects.create(name="Maize")
    chief = SystemUser.objects.create_user(
        phone="+256700000110", full_name="Chief", role=Role.PARISH_CHIEF,
        scope_level=ScopeLevel.PARISH, scope_id=parish.id)
    farmer = Farmer.objects.create(village=village, full_name="Grace Nabirye", sex="F", registered_by=chief)
    district_officer = SystemUser.objects.create_user(
        phone="+256700000111", password="pin1234", full_name="DO",
        role=Role.DISTRICT_OFFICER, scope_level=ScopeLevel.DISTRICT, scope_id=district.id)
    other_district_officer = SystemUser.objects.create_user(
        phone="+256700000112", password="pin1234", full_name="Other DO",
        role=Role.DISTRICT_OFFICER, scope_level=ScopeLevel.DISTRICT, scope_id=other_district.id)
    national_admin = SystemUser.objects.create_user(
        phone="+256700000113", password="pin1234", full_name="NA",
        role=Role.NATIONAL_ADMIN, scope_level=ScopeLevel.NATIONAL)
    insight = TrendInsight.objects.create(
        scope_level=ScopeLevel.PARISH, scope_id=parish.id, crop=crop, metric="avg_price_per_kg",
        direction="up", magnitude="5.00", window_weeks=3, message="Prices are rising in Katosi.")
    return {"district": district, "parish": parish, "farmer": farmer, "crop": crop,
            "district_officer": district_officer, "other_district_officer": other_district_officer,
            "national_admin": national_admin, "insight": insight}


def _client(user):
    client = APIClient()
    client.post("/api/v1/auth/login/", {"phone": user.phone, "password": "pin1234"}, format="json")
    return client


@pytest.mark.django_db
def test_approve_publishes_and_delivers_to_farmers_in_scope(world):
    approve_insight(insight_id=world["insight"].id, actor=world["district_officer"])
    world["insight"].refresh_from_db()
    assert world["insight"].published_at is not None
    assert world["insight"].approved_by == world["district_officer"]
    assert AdvisoryDelivery.objects.filter(trend=world["insight"], farmer=world["farmer"]).exists()


@pytest.mark.django_db
def test_approve_twice_is_rejected(world):
    approve_insight(insight_id=world["insight"].id, actor=world["district_officer"])
    with pytest.raises(TrendApprovalError):
        approve_insight(insight_id=world["insight"].id, actor=world["district_officer"])


@pytest.mark.django_db
def test_farmer_cannot_approve():
    farmer_user = SystemUser.objects.create_user(
        phone="+256700000114", full_name="Farmer", role=Role.FARMER, scope_level=ScopeLevel.NATIONAL)
    with pytest.raises(TrendApprovalError):
        approve_insight(insight_id=1, actor=farmer_user)


@pytest.mark.django_db
def test_approve_endpoint_publishes(world):
    res = _client(world["district_officer"]).post(f"/api/v1/trends/{world['insight'].id}/approve/")
    assert res.status_code == 200
    assert res.data["published_at"] is not None
    assert res.data["approved_by"] == "DO"


@pytest.mark.django_db
def test_approve_endpoint_rejects_farmer_role(world):
    farmer_user = SystemUser.objects.create_user(
        phone="+256700000115", password="pin1234", full_name="Farmer",
        role=Role.FARMER, scope_level=ScopeLevel.PARISH, scope_id=world["parish"].id)
    res = _client(farmer_user).post(f"/api/v1/trends/{world['insight'].id}/approve/")
    assert res.status_code == 403


@pytest.mark.django_db
def test_approve_endpoint_rejects_already_published(world):
    client = _client(world["district_officer"])
    client.post(f"/api/v1/trends/{world['insight'].id}/approve/")
    res = client.post(f"/api/v1/trends/{world['insight'].id}/approve/")
    assert res.status_code == 409


@pytest.mark.django_db
def test_pending_list_is_scoped_to_the_officers_own_district(world):
    res = _client(world["district_officer"]).get("/api/v1/trends/?status=pending")
    assert [t["id"] for t in res.data] == [world["insight"].id]

    res_other = _client(world["other_district_officer"]).get("/api/v1/trends/?status=pending")
    assert res_other.data == []


@pytest.mark.django_db
def test_national_admin_sees_all_pending(world):
    res = _client(world["national_admin"]).get("/api/v1/trends/?status=pending")
    assert [t["id"] for t in res.data] == [world["insight"].id]


@pytest.mark.django_db
def test_published_list_excludes_drafts(world):
    _client(world["district_officer"]).post(f"/api/v1/trends/{world['insight'].id}/approve/")
    res = _client(world["national_admin"]).get("/api/v1/trends/?status=published")
    assert [t["id"] for t in res.data] == [world["insight"].id]

    pending = _client(world["national_admin"]).get("/api/v1/trends/?status=pending")
    assert pending.data == []
