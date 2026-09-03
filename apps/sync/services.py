from apps.advisory.selectors import current_season
from apps.farmers.models import Crop, Farmer
from apps.farmers.services import register_farmer
from apps.geo.models import Village
from apps.market.models import Declaration
from apps.market.services import DomainError, declare, record_grading


class SyncRejected(Exception):
    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(reason)


def apply_operation(op_type: str, payload: dict, *, actor) -> dict:
    handler = _HANDLERS.get(op_type)
    if handler is None:
        raise SyncRejected("unknown_operation_type")
    return handler(payload, actor)


def _apply_farmer_create(payload, actor):
    try:
        village = Village.objects.get(pk=payload["village_id"])
    except (KeyError, Village.DoesNotExist):
        raise SyncRejected("invalid_payload") from None

    crop = planting_date = area_acres = season = None
    if payload.get("crop_id"):
        crop = Crop.objects.filter(pk=payload["crop_id"]).first()
        planting_date = payload.get("planting_date")
        area_acres = payload.get("area_acres")
        season = current_season()

    farmer, created = register_farmer(
        full_name=payload["full_name"], village=village, sex=payload["sex"],
        language=payload.get("language", "lug"), reach_channel=payload.get("reach_channel", "agent"),
        phone=payload.get("phone"), registered_by=actor,
        crop=crop, planting_date=planting_date, area_acres=area_acres, season=season)
    return {"farmer_id": farmer.id, "created": created}


def _apply_declaration_create(payload, actor):
    try:
        farmer = Farmer.objects.get(pk=payload["farmer_id"])
        crop = Crop.objects.get(pk=payload["crop_id"])
        bags = payload["bags"]
    except (KeyError, Farmer.DoesNotExist, Crop.DoesNotExist):
        raise SyncRejected("invalid_payload") from None
    try:
        d = declare(farmer=farmer, crop=crop, bags=bags, moisture=payload.get("moisture_pct"),
                    actor=actor, via="agent")
    except DomainError:
        raise SyncRejected("lot_closed") from None
    return {"declaration_id": d.id, "grade": d.grade}


def _apply_declaration_grade(payload, actor):
    try:
        declaration_id = payload["declaration_id"]
        moisture = payload["moisture_pct"]
    except KeyError:
        raise SyncRejected("invalid_payload") from None
    try:
        d = record_grading(declaration_id=declaration_id, moisture=moisture, actor=actor)
    except Declaration.DoesNotExist:
        raise SyncRejected("invalid_payload") from None
    except DomainError:
        raise SyncRejected("lot_closed") from None
    return {"declaration_id": d.id, "grade": d.grade}


_HANDLERS = {
    "farmer.create": _apply_farmer_create,
    "declaration.create": _apply_declaration_create,
    "declaration.grade": _apply_declaration_grade,
}
