from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import Role
from apps.farmers.models import Crop
from apps.farmers.selectors import farmers_for_parishes
from apps.geo.models import Village
from apps.market.models import Lot, LotStatus
from apps.realtime.events import now_iso
from apps.sync.models import SyncOperation
from apps.sync.serializers import (
    BootstrapSerializer,
    SyncBatchRequestSerializer,
    SyncBatchResponseSerializer,
)
from apps.sync.services import SyncRejected, apply_operation


class IsAgent(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == Role.AGENT)


class BootstrapView(APIView):
    """Everything an agent's device caches before going into the field:
    their parish roster, crop reference data, and the open lot(s)
    (IMPLEMENTATION.md section 9: "Cache on bootstrap")."""

    permission_classes = [IsAgent]

    @extend_schema(responses={200: BootstrapSerializer})
    def get(self, request):
        parish_id = request.user.scope_id
        if parish_id is None:
            raise ValidationError("This agent has no parish assigned.")
        data = {
            "parish_id": parish_id,
            "villages": Village.objects.filter(parish_id=parish_id).order_by("name"),
            "crops": Crop.objects.all().order_by("name"),
            "farmers": farmers_for_parishes([parish_id]),
            "open_lots": Lot.objects.filter(parish_id=parish_id, status=LotStatus.OPEN).select_related("crop"),
        }
        return Response(BootstrapSerializer(data).data)


class SyncBatchView(APIView):
    permission_classes = [IsAgent]

    @extend_schema(request=SyncBatchRequestSerializer, responses={200: SyncBatchResponseSerializer})
    def post(self, request):
        data = SyncBatchRequestSerializer(data=request.data)
        data.is_valid(raise_exception=True)

        results = []
        for op in data.validated_data["operations"]:
            op_id = op["op_id"]
            existing = SyncOperation.objects.filter(op_id=op_id).first()
            if existing:
                results.append({"op_id": op_id, "status": existing.status,
                                 **({"reason": existing.reason} if existing.reason else {}),
                                 **existing.result})
                continue
            try:
                result = apply_operation(op["type"], op["payload"], actor=request.user)
                SyncOperation.objects.create(op_id=op_id, device_id=data.validated_data["device_id"],
                                             op_type=op["type"], submitted_by=request.user,
                                             status="applied", result=result)
                results.append({"op_id": op_id, "status": "applied", **result})
            except SyncRejected as e:
                SyncOperation.objects.create(op_id=op_id, device_id=data.validated_data["device_id"],
                                             op_type=op["type"], submitted_by=request.user,
                                             status="rejected", reason=e.reason)
                results.append({"op_id": op_id, "status": "rejected", "reason": e.reason})

        return Response(SyncBatchResponseSerializer({"results": results, "server_time": now_iso()}).data)
