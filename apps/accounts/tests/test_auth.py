import pytest
from rest_framework.test import APIClient

from apps.accounts.models import Role, ScopeLevel, SystemUser
from config.settings.base import JWT_ACCESS_COOKIE, JWT_REFRESH_COOKIE


@pytest.fixture
def user(db):
    return SystemUser.objects.create_user(
        phone="+256700000010", password="pin1234", full_name="Nat Admin",
        role=Role.NATIONAL_ADMIN, scope_level=ScopeLevel.NATIONAL,
    )


@pytest.mark.django_db
def test_login_sets_httponly_cookies_and_returns_profile(user):
    client = APIClient()
    res = client.post("/api/v1/auth/login/", {"phone": user.phone, "password": "pin1234"}, format="json")
    assert res.status_code == 200
    assert res.data["role"] == Role.NATIONAL_ADMIN
    assert res.data["permissions"] == ["trend.approve", "metrics.national.view", "metrics.district.view", "parish.view", "admin.manage"]
    assert res.cookies[JWT_ACCESS_COOKIE]["httponly"]
    assert res.cookies[JWT_REFRESH_COOKIE]["httponly"]


@pytest.mark.django_db
def test_login_wrong_password_returns_401(user):
    client = APIClient()
    res = client.post("/api/v1/auth/login/", {"phone": user.phone, "password": "wrong"}, format="json")
    assert res.status_code == 401


@pytest.mark.django_db
def test_me_requires_the_access_cookie(user):
    client = APIClient()
    assert client.get("/api/v1/me/").status_code == 401
    client.post("/api/v1/auth/login/", {"phone": user.phone, "password": "pin1234"}, format="json")
    res = client.get("/api/v1/me/")
    assert res.status_code == 200
    assert res.data["id"] == user.id


@pytest.mark.django_db
def test_refresh_rotates_the_access_cookie(user):
    client = APIClient()
    client.post("/api/v1/auth/login/", {"phone": user.phone, "password": "pin1234"}, format="json")
    old_access = client.cookies[JWT_ACCESS_COOKIE].value
    res = client.post("/api/v1/auth/refresh/")
    assert res.status_code == 204
    assert client.cookies[JWT_ACCESS_COOKIE].value != old_access
    assert client.get("/api/v1/me/").status_code == 200


@pytest.mark.django_db
def test_logout_clears_cookies_and_blacklists_refresh(user):
    client = APIClient()
    client.post("/api/v1/auth/login/", {"phone": user.phone, "password": "pin1234"}, format="json")
    res = client.post("/api/v1/auth/logout/")
    assert res.status_code == 204
    assert client.post("/api/v1/auth/refresh/").status_code == 401
