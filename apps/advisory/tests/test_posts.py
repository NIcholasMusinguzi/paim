import pytest
from rest_framework.test import APIClient

from apps.accounts.models import Role, ScopeLevel, SystemUser
from apps.geo.models import District, Parish, Subcounty, Village


@pytest.fixture
def world(db):
    mukono = District.objects.create(name="Mukono")
    wakiso = District.objects.create(name="Wakiso")
    kyampisi = Subcounty.objects.create(district=mukono, name="Kyampisi")
    katosi = Parish.objects.create(subcounty=kyampisi, name="Katosi")
    other_parish = Parish.objects.create(subcounty=kyampisi, name="Elsewhere")
    wakiso_subcounty = Subcounty.objects.create(district=wakiso, name="Nabweru")
    wakiso_parish = Parish.objects.create(subcounty=wakiso_subcounty, name="Kazo")
    village = Village.objects.create(parish=katosi, name="Kigunga")

    chief = SystemUser.objects.create_user(
        phone="+256700001000", password="pin1234", full_name="Chief",
        role=Role.PARISH_CHIEF, scope_level=ScopeLevel.PARISH, scope_id=katosi.id)
    other_chief = SystemUser.objects.create_user(
        phone="+256700001001", password="pin1234", full_name="Other Chief",
        role=Role.PARISH_CHIEF, scope_level=ScopeLevel.PARISH, scope_id=wakiso_parish.id)
    district_officer = SystemUser.objects.create_user(
        phone="+256700001002", password="pin1234", full_name="DO",
        role=Role.DISTRICT_OFFICER, scope_level=ScopeLevel.DISTRICT, scope_id=mukono.id)
    national_admin = SystemUser.objects.create_user(
        phone="+256700001003", password="pin1234", full_name="NA",
        role=Role.NATIONAL_ADMIN, scope_level=ScopeLevel.NATIONAL)
    farmer_user = SystemUser.objects.create_user(
        phone="+256700001004", password="pin1234", full_name="Grace Nabirye",
        role=Role.FARMER, scope_level=ScopeLevel.PARISH, scope_id=katosi.id)
    from apps.farmers.models import Farmer

    farmer = Farmer.objects.create(village=village, full_name="Grace Nabirye", sex="F",
                                   registered_by=chief, user=farmer_user)

    return {"mukono": mukono, "wakiso": wakiso, "katosi": katosi, "other_parish": other_parish,
            "wakiso_parish": wakiso_parish, "chief": chief, "other_chief": other_chief,
            "district_officer": district_officer, "national_admin": national_admin,
            "farmer_user": farmer_user, "farmer": farmer}


def _client(user):
    client = APIClient()
    client.post("/api/v1/auth/login/", {"phone": user.phone, "password": "pin1234"}, format="json")
    return client


@pytest.mark.django_db
def test_chief_can_post_to_their_own_parish(world):
    res = _client(world["chief"]).post("/api/v1/posts/", {
        "scope_level": "parish", "scope_id": world["katosi"].id,
        "title": "Spraying day", "body": "Bring your own equipment.",
    }, format="json")
    assert res.status_code == 201
    assert res.data["author_name"] == "Chief"


@pytest.mark.django_db
def test_chief_cannot_post_to_another_parish(world):
    res = _client(world["chief"]).post("/api/v1/posts/", {
        "scope_level": "parish", "scope_id": world["wakiso_parish"].id,
        "title": "Spraying day", "body": "Bring your own equipment.",
    }, format="json")
    assert res.status_code == 403


@pytest.mark.django_db
def test_chief_cannot_post_nationally(world):
    res = _client(world["chief"]).post("/api/v1/posts/", {
        "scope_level": "national", "title": "Hello", "body": "Everyone hi.",
    }, format="json")
    assert res.status_code == 403


@pytest.mark.django_db
def test_national_admin_can_post_anywhere(world):
    res = _client(world["national_admin"]).post("/api/v1/posts/", {
        "scope_level": "parish", "scope_id": world["wakiso_parish"].id,
        "title": "National notice", "body": "Applies to Kazo.",
    }, format="json")
    assert res.status_code == 201


@pytest.mark.django_db
def test_farmer_cannot_post(world):
    res = _client(world["farmer_user"]).post("/api/v1/posts/", {
        "scope_level": "parish", "scope_id": world["katosi"].id,
        "title": "x", "body": "y",
    }, format="json")
    assert res.status_code == 403


@pytest.mark.django_db
def test_farmer_sees_their_parish_and_district_and_national_posts_only(world):
    client = _client(world["chief"])
    client.post("/api/v1/posts/", {"scope_level": "parish", "scope_id": world["katosi"].id,
                                    "title": "Parish post", "body": "b"}, format="json")
    _client(world["district_officer"]).post("/api/v1/posts/", {
        "scope_level": "district", "scope_id": world["mukono"].id,
        "title": "District post", "body": "b"}, format="json")
    _client(world["national_admin"]).post("/api/v1/posts/", {
        "scope_level": "national", "title": "National post", "body": "b"}, format="json")
    _client(world["other_chief"]).post("/api/v1/posts/", {
        "scope_level": "parish", "scope_id": world["wakiso_parish"].id,
        "title": "Other parish post", "body": "b"}, format="json")

    res = _client(world["farmer_user"]).get("/api/v1/posts/")
    titles = {p["title"] for p in res.data}
    assert titles == {"Parish post", "District post", "National post"}


@pytest.mark.django_db
def test_any_signed_in_user_can_comment_on_a_visible_post(world):
    chief_client = _client(world["chief"])
    post = chief_client.post("/api/v1/posts/", {
        "scope_level": "parish", "scope_id": world["katosi"].id, "title": "Spraying day", "body": "b",
    }, format="json").data

    farmer_client = _client(world["farmer_user"])
    comment = farmer_client.post(f"/api/v1/posts/{post['id']}/comments/", {"body": "What time?"}, format="json")
    assert comment.status_code == 201
    assert comment.data["author_name"] == "Grace Nabirye"

    listing = chief_client.get(f"/api/v1/posts/{post['id']}/comments/")
    assert [c["body"] for c in listing.data] == ["What time?"]


@pytest.mark.django_db
def test_cannot_comment_on_a_post_outside_your_scope(world):
    post = _client(world["other_chief"]).post("/api/v1/posts/", {
        "scope_level": "parish", "scope_id": world["wakiso_parish"].id, "title": "x", "body": "y",
    }, format="json").data

    res = _client(world["farmer_user"]).post(f"/api/v1/posts/{post['id']}/comments/", {"body": "hi"}, format="json")
    assert res.status_code == 404
