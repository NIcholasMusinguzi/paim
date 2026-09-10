import json
from datetime import date
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.core.cache import cache

KAMPALA = (0.3476, 32.5825)
FORECAST_TTL = 45 * 60
COORDS_TTL = 7 * 24 * 3600
USER_AGENT = "PAIM/1.0 (+https://paim.local)"


class WeatherError(Exception):
    pass


def _http_json(url: str) -> dict:
    req = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    try:
        with urlopen(req, timeout=8) as resp:
            return json.loads(resp.read().decode())
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise WeatherError("Weather service is unavailable.") from exc


def icon_for(code: int) -> tuple[str, str]:
    if code in (0, 1):
        return "sun", "Clear" if code == 0 else "Mainly clear"
    if code == 2:
        return "cloud", "Partly cloudy"
    if code in (3, 45, 48):
        return "cloud", "Overcast" if code == 3 else "Fog"
    if 51 <= code <= 67 or 80 <= code <= 99:
        return "rain", "Rain"
    if 71 <= code <= 77 or 85 <= code <= 86:
        return "cloud", "Precipitation"
    return "cloud", "Cloudy"


def geocode_parish(parish) -> tuple[float, float]:
    key = f"geo:coords:{parish.id}"
    cached = cache.get(key)
    if cached:
        return cached
    queries = [f"{parish.name}, Uganda", f"{parish.district.name}, Uganda"]
    for query in queries:
        data = _http_json(
            "https://geocoding-api.open-meteo.com/v1/search?"
            + urlencode({"name": query, "count": 1, "countryCode": "UG"})
        )
        results = data.get("results") or []
        if results:
            coords = (float(results[0]["latitude"]), float(results[0]["longitude"]))
            cache.set(key, coords, COORDS_TTL)
            return coords
    coords = KAMPALA
    cache.set(key, coords, COORDS_TTL)
    return coords


def forecast_at(lat: float, lon: float) -> dict:
    key = f"weather:forecast:{lat:.2f}:{lon:.2f}"
    cached = cache.get(key)
    if cached:
        return cached
    params = urlencode({
        "latitude": f"{lat:.4f}",
        "longitude": f"{lon:.4f}",
        "current": "temperature_2m,relative_humidity_2m,precipitation,weather_code,wind_speed_10m",
        "daily": "weather_code,temperature_2m_max",
        "forecast_days": 5,
        "timezone": "Africa/Kampala",
    })
    data = _http_json(f"https://api.open-meteo.com/v1/forecast?{params}")
    current = data.get("current") or {}
    daily = data.get("daily") or {}
    code = int(current.get("weather_code") or 2)
    icon, summary = icon_for(code)
    days = daily.get("time") or []
    codes = daily.get("weather_code") or []
    highs = daily.get("temperature_2m_max") or []
    forecast = []
    for i, day in enumerate(days[:5]):
        d_icon, _ = icon_for(int(codes[i] if i < len(codes) else 2))
        label = date.fromisoformat(day).strftime("%a")
        hi = highs[i] if i < len(highs) else None
        forecast.append({"day": label, "icon": d_icon, "hi": round(hi) if hi is not None else None})
    payload = {
        "temp_c": round(float(current.get("temperature_2m") or 0)),
        "summary": summary,
        "icon": icon,
        "humidity": int(current.get("relative_humidity_2m") or 0),
        "rain_mm": round(float(current.get("precipitation") or 0)),
        "wind_kmh": round(float(current.get("wind_speed_10m") or 0)),
        "forecast": forecast,
    }
    cache.set(key, payload, FORECAST_TTL)
    return payload


def weather_for_parish(parish) -> dict:
    lat, lon = geocode_parish(parish) if parish else KAMPALA
    payload = forecast_at(lat, lon)
    place = f"{parish.name} parish" if parish else "Kampala, Uganda"
    return {"place": place, **payload}
