from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import Role, ScopeLevel, SystemUser
from apps.market.models import MarketPrice


@pytest.fixture
def officer(db):
    return SystemUser.objects.create_user(
        phone="+256700000280", password="pin1234", full_name="Officer",
        role=Role.NATIONAL_ADMIN, scope_level=ScopeLevel.NATIONAL)


def _client(user):
    client = APIClient()
    client.post("/api/v1/auth/login/", {"phone": user.phone, "password": "pin1234"}, format="json")
    return client


@pytest.mark.django_db
def test_daily_prices_return_latest_per_item_when_no_date(officer):
    today = timezone.localdate()
    MarketPrice.objects.create(
        item_name="Maize", category="produce", price=1000, unit="UGX/kg",
        market="Katosi", price_date=today - timedelta(days=3), source="old")
    MarketPrice.objects.create(
        item_name="Maize", category="produce", price=1150, unit="UGX/kg",
        market="Katosi", price_date=today, source="new")
    MarketPrice.objects.create(
        item_name="Beans", category="produce", price=3200, unit="UGX/kg",
        market="Nakasero", price_date=today - timedelta(days=1), source="survey")
    res = _client(officer).get("/api/v1/market-prices/daily/")
    assert res.status_code == 200
    by_name = {row["item_name"]: row["price"] for row in res.data}
    assert by_name["Maize"] == 1150
    assert by_name["Beans"] == 3200


@pytest.mark.django_db
def test_daily_prices_filter_by_date(officer):
    today = timezone.localdate()
    MarketPrice.objects.create(
        item_name="Maize", category="produce", price=1000, unit="UGX/kg",
        market="Katosi", price_date=today - timedelta(days=1), source="old")
    MarketPrice.objects.create(
        item_name="Maize", category="produce", price=1150, unit="UGX/kg",
        market="Katosi", price_date=today, source="new")
    res = _client(officer).get(f"/api/v1/market-prices/daily/?date={today.isoformat()}")
    assert res.status_code == 200
    assert [row["price"] for row in res.data] == [1150]
