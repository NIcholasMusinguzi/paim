from unittest.mock import patch

import pytest
from django.core.cache import cache
from rest_framework.test import APIClient

from apps.accounts.models import Role, ScopeLevel, SystemUser
from apps.geo.models import District, Parish, Subcounty
from apps.geo.weather import icon_for

GEOCODE = {"results": [{"latitude": 0.35, "longitude": 32.75}]}
FORECAST = {
    "current": {
        "temperature_2m": 27.4,
        "relative_humidity_2m": 61,
        "precipitation": 1.2,
        "weather_code": 2,
        "wind_speed_10m": 11.6,
    },
    "daily": {
        "time": ["2026-09-10", "2026-09-11", "2026-09-12", "2026-09-13", "2026-09-14"],
        "weather_code": [2, 61, 0, 3, 1],
        "temperature_2m_max": [28.1, 24.0, 30.2, 26.4, 29.0],
    },
}


@pytest.fixture
def world(db):
    cache.clear()
    district = District.objects.create(name="Mukono")
    subcounty = Subcounty.objects.create(district=district, name="Kyampisi")
    parish = Parish.objects.create(subcounty=subcounty, name="Katosi")
    user = SystemUser.objects.create_user(
        phone="+256700000210", password="pin1234", full_name="Chief",
        role=Role.PARISH_CHIEF, scope_level=ScopeLevel.PARISH, scope_id=parish.id)
    return {"parish": parish, "user": user}


def _client(user):
    client = APIClient()
    client.post("/api/v1/auth/login/", {"phone": user.phone, "password": "pin1234"}, format="json")
    return client


def test_icon_for_maps_wmo_codes():
    assert icon_for(0) == ("sun", "Clear")
    assert icon_for(2)[0] == "cloud"
    assert icon_for(61)[0] == "rain"


@pytest.mark.django_db
@patch("apps.geo.weather._http_json", side_effect=[GEOCODE, FORECAST])
def test_weather_uses_open_meteo_payload(mock_http, world):
    res = _client(world["user"]).get("/api/v1/weather/")
    assert res.status_code == 200
    assert res.data["place"] == "Katosi parish"
    assert res.data["temp_c"] == 27
    assert res.data["icon"] == "cloud"
    assert res.data["forecast"][1]["icon"] == "rain"
    assert mock_http.call_count == 2
