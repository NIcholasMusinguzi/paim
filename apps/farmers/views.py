from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import NotFound
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import Role
from apps.farmers.models import Crop, Season
from apps.farmers.selectors import farmer_home
from apps.farmers.serializers import (
    FarmerHomeSerializer,
    ReferenceDataSerializer,
)


class IsFarmer(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == Role.FARMER)


class FarmerHomeView(APIView):
    permission_classes = [IsFarmer]

    @extend_schema(responses={200: FarmerHomeSerializer})
    def get(self, request):
        farmer = getattr(request.user, "farmer_profile", None)
        if farmer is None:
            raise NotFound("No farmer profile is linked to this account.")
        return Response(FarmerHomeSerializer(farmer_home(farmer)).data)


class ReferenceDataView(APIView):
    """Seasons and crops for populating pickers (the national dashboard's
    ?season=&crop= filter, in particular). Not role-restricted — every
    authenticated role needs this to use scoped, filtered endpoints."""

    @extend_schema(responses={200: ReferenceDataSerializer})
    def get(self, request):
        data = {
            "seasons": Season.objects.order_by("-year", "-season_no"),
            "crops": Crop.objects.order_by("name"),
        }
        return Response(ReferenceDataSerializer(data).data)
