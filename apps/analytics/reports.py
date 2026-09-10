from django.db.models import Avg, Count, Sum

from apps.accounts.models import Role
from apps.accounts.scoping import parish_ids_for
from apps.advisory.selectors import advisory_requests_visible_to
from apps.analytics.models import ParishSeasonMetric
from apps.farmers.selectors import farmers_for_parishes
from apps.geo.models import Parish
from apps.geo.weather import WeatherError, weather_for_parish
from apps.market.models import LotStatus, MarketPrice
from apps.market.selectors import lots_for_viewer
from apps.market.services import sellable_bags, visible_bids


def _scoped_parish_ids(user, district_id=None):
    qs = Parish.objects.filter(id__in=parish_ids_for(user))
    if district_id:
        qs = qs.filter(subcounty__district_id=district_id)
    return qs.values_list("id", flat=True)


def _lots_qs(user, district_id=None, season_id=None, crop_id=None):
    qs = lots_for_viewer(user)
    if district_id:
        if user.role == Role.BUYER:
            qs = qs.filter(parish__subcounty__district_id=district_id)
        else:
            qs = qs.filter(parish_id__in=_scoped_parish_ids(user, district_id))
    if season_id:
        qs = qs.filter(season_id=season_id)
    if crop_id:
        qs = qs.filter(crop_id=crop_id)
    return qs


def _parishes(user):
    return (
        Parish.objects.filter(id__in=parish_ids_for(user))
        .select_related("subcounty__district")
        .order_by("subcounty__district__name", "subcounty__name", "name")
    )


def _region(parish) -> dict:
    return {
        "district": parish.subcounty.district.name,
        "subcounty": parish.subcounty.name,
        "parish": parish.name,
    }


def farmers_report(user, district_id=None, **_):
    headers = ["District", "Subcounty", "Parish", "Village", "Farmer", "Sex", "Phone"]
    if user.role == Role.BUYER:
        return "paim-farmers", "Farmers", headers, [], []
    payload = []
    for farmer in farmers_for_parishes(_scoped_parish_ids(user, district_id)).select_related(
            "village__parish__subcounty__district"):
        loc = _region(farmer.village.parish)
        payload.append({
            **loc,
            "village": farmer.village.name,
            "farmer": farmer.full_name,
            "sex": farmer.sex,
            "phone": farmer.phone or "—",
        })
    rows = [[r["district"], r["subcounty"], r["parish"], r["village"], r["farmer"], r["sex"], r["phone"]]
            for r in payload]
    return "paim-farmers", "Farmers", headers, payload, rows


def bids_report(user, district_id=None, **_):
    headers = ["District", "Subcounty", "Parish", "Crop", "Lot status", "Buyer", "UGX/kg", "Terms"]
    payload = []
    for lot in _lots_qs(user, district_id=district_id).prefetch_related("bids__buyer"):
        loc = _region(lot.parish)
        disclosed = list(visible_bids(lot, user))
        if lot.status == LotStatus.OPEN and not disclosed:
            payload.append({
                **loc, "crop": lot.crop.name, "lot_status": lot.status,
                "buyer": f"{lot.bids.count()} sealed", "price_per_kg": None, "terms": "—",
            })
            continue
        if not disclosed:
            payload.append({
                **loc, "crop": lot.crop.name, "lot_status": lot.status,
                "buyer": "—", "price_per_kg": None, "terms": "—",
            })
            continue
        for bid in disclosed:
            payload.append({
                **loc, "crop": lot.crop.name, "lot_status": lot.status,
                "buyer": bid.buyer.name, "price_per_kg": bid.price_per_kg, "terms": bid.terms,
            })
    rows = [[r["district"], r["subcounty"], r["parish"], r["crop"], r["lot_status"],
             r["buyer"], r["price_per_kg"], r["terms"]] for r in payload]
    return "paim-bids", "Bids", headers, payload, rows


def prices_report(user, season_id=None, crop_id=None, **_):
    headers = ["District", "Subcounty", "Parish", "Crop", "UGX/kg", "Bags", "Grade 1 %"]
    qs = ParishSeasonMetric.objects.filter(
        parish_id__in=parish_ids_for(user),
    ).select_related("parish__subcounty__district", "crop")
    if season_id:
        qs = qs.filter(season_id=season_id)
    if crop_id:
        qs = qs.filter(crop_id=crop_id)
    payload = []
    for row in qs.order_by("crop__name", "parish__name"):
        loc = _region(row.parish)
        payload.append({
            **loc, "crop": row.crop.name, "avg_price_per_kg": row.avg_price_per_kg,
            "bags_declared": row.bags_declared, "pct_grade1": row.pct_grade1,
        })
    if not payload:
        latest = MarketPrice.objects.filter(category=MarketPrice.Category.PRODUCE).order_by("-price_date")
        seen = set()
        for price in latest:
            if price.item_name in seen:
                continue
            seen.add(price.item_name)
            payload.append({
                "district": "—", "subcounty": "—", "parish": "—",
                "crop": price.item_name, "avg_price_per_kg": price.price,
                "bags_declared": None, "pct_grade1": None,
            })
    rows = [[r["district"], r["subcounty"], r["parish"], r["crop"],
             r["avg_price_per_kg"], r["bags_declared"], r["pct_grade1"]] for r in payload]
    return "paim-crop-prices", "Market prices by crop", headers, payload, rows


def lots_report(user, season_id=None, crop_id=None, district_id=None, **_):
    headers = ["District", "Subcounty", "Parish", "Crop", "Status", "Bags", "Bids", "Awarded buyer", "UGX/kg"]
    qs = _lots_qs(user, district_id=district_id, season_id=season_id, crop_id=crop_id)
    payload = []
    for lot in qs:
        loc = _region(lot.parish)
        bid = lot.awarded_bid if lot.awarded_bid_id else None
        payload.append({
            **loc, "crop": lot.crop.name, "status": lot.status,
            "bags": sellable_bags(lot),
            "bid_count": getattr(lot, "_bid_count", lot.bids.count()),
            "awarded_buyer": bid.buyer.name if bid else None,
            "awarded_price_per_kg": bid.price_per_kg if bid else None,
        })
    rows = [[r["district"], r["subcounty"], r["parish"], r["crop"], r["status"],
             r["bags"], r["bid_count"], r["awarded_buyer"], r["awarded_price_per_kg"]] for r in payload]
    return "paim-lots", "Lots", headers, payload, rows


def crops_report(user, season_id=None, **_):
    headers = ["Crop", "Parishes", "Bags", "Active farmers", "Avg UGX/kg"]
    qs = ParishSeasonMetric.objects.filter(parish_id__in=parish_ids_for(user))
    if season_id:
        qs = qs.filter(season_id=season_id)
    payload = []
    for row in (
        qs.values("crop_id", "crop__name")
        .annotate(bags=Sum("bags_declared"), farmers=Sum("farmers_active"),
                  avg_price=Avg("avg_price_per_kg"))
        .order_by("-bags")
    ):
        parishes = qs.filter(crop_id=row["crop_id"]).values("parish_id").distinct().count()
        avg = row["avg_price"]
        payload.append({
            "crop": row["crop__name"],
            "parishes": parishes,
            "bags": row["bags"] or 0,
            "farmers_active": row["farmers"] or 0,
            "avg_price_per_kg": round(avg) if avg is not None else None,
        })
    rows = [[r["crop"], r["parishes"], r["bags"], r["farmers_active"], r["avg_price_per_kg"]] for r in payload]
    return "paim-top-crops", "Top crops", headers, payload, rows


def weather_report(user, **_):
    headers = ["District", "Subcounty", "Parish", "Temp °C", "Summary", "Rain mm", "Insight"]
    payload = []
    for parish in _parishes(user)[:60]:
        loc = _region(parish)
        try:
            w = weather_for_parish(parish)
            rain = w["rain_mm"]
            temp = w["temp_c"]
            if rain >= 8:
                insight = "Heavy rain — delay harvest and spraying."
            elif rain >= 2:
                insight = "Light rain — good for planting; watch leaf disease."
            elif temp >= 30:
                insight = "Hot and dry — irrigate where possible."
            else:
                insight = "Fair conditions for field work."
            payload.append({
                **loc, "temp_c": temp, "summary": w["summary"], "rain_mm": rain, "insight": insight,
            })
        except WeatherError:
            payload.append({
                **loc, "temp_c": None, "summary": "Unavailable", "rain_mm": None,
                "insight": "Weather service is unavailable.",
            })
    rows = [[r["district"], r["subcounty"], r["parish"], r["temp_c"], r["summary"],
             r["rain_mm"], r["insight"]] for r in payload]
    return "paim-weather-insights", "Weather insights", headers, payload, rows


def scoped_report(user, season_id=None, crop_id=None, **_):
    headers = ["District", "Subcounty", "Parish", "Farmers", "Active", "Bags", "Grade 1 %", "UGX/kg"]
    qs = ParishSeasonMetric.objects.filter(
        parish_id__in=parish_ids_for(user),
    ).select_related("parish__subcounty__district")
    if season_id:
        qs = qs.filter(season_id=season_id)
    if crop_id:
        qs = qs.filter(crop_id=crop_id)
    payload = []
    for row in qs.order_by("parish__name"):
        loc = _region(row.parish)
        payload.append({
            **loc, "id": row.id, "parish_id": row.parish_id,
            "farmers_registered": row.farmers_registered, "farmers_active": row.farmers_active,
            "bags_declared": row.bags_declared, "pct_grade1": row.pct_grade1,
            "avg_price_per_kg": row.avg_price_per_kg,
            "computed_at": row.computed_at,
        })
    rows = [[r["district"], r["subcounty"], r["parish"], r["farmers_registered"],
             r["farmers_active"], r["bags_declared"], r["pct_grade1"], r["avg_price_per_kg"]]
            for r in payload]
    return "paim-parish-performance", "Parish performance", headers, payload, rows


def advisories_report(user, **_):
    headers = ["Parish", "Requester", "Status", "Responses", "Message"]
    payload = []
    for item in advisory_requests_visible_to(user).annotate(response_count=Count("responses")):
        parish = item.farmer.village.parish.name if item.farmer_id else "—"
        requester = (
            item.farmer.full_name if item.farmer_id
            else (item.requester.full_name if item.requester_id else "—")
        )
        payload.append({
            "id": item.id, "parish": parish, "requester": requester,
            "status": item.status, "response_count": item.response_count, "message": item.message,
        })
    rows = [[r["parish"], r["requester"], r["status"], r["response_count"], r["message"][:80]] for r in payload]
    return "paim-advisory-activity", "Advisory activity", headers, payload, rows


BUILDERS = {
    "farmers": farmers_report,
    "bids": bids_report,
    "prices": prices_report,
    "lots": lots_report,
    "market": lots_report,
    "crops": crops_report,
    "weather": weather_report,
    "scoped": scoped_report,
    "advisories": advisories_report,
}
