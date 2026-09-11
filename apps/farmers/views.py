from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import Role
from apps.accounts.permissions import IsOfficer
from apps.accounts.scoping import parish_ids_for
from apps.farmers.models import Crop, Planting, Plot, Season
from apps.farmers.selectors import farmer_home, farmers_for_parishes
from apps.farmers.serializers import (
    FarmerDirectorySerializer,
    FarmerHomeSerializer,
    ReferenceDataSerializer,
    FarmerDeclarationSerializer,
    FarmerProfileSerializer,
)
from apps.market.models import Lot
from apps.market.services import DomainError, declare


class IsFarmer(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == Role.FARMER)


class FarmerDirectoryView(APIView):
    permission_classes = [IsOfficer]

    @extend_schema(responses={200: FarmerDirectorySerializer(many=True)})
    def get(self, request):
        farmers = (
            farmers_for_parishes(parish_ids_for(request.user))
            .select_related("village__parish__subcounty__district")
            .order_by("full_name")
        )
        return Response(FarmerDirectorySerializer(farmers, many=True).data)


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


def farmer_for(request):
    farmer = getattr(request.user, "farmer_profile", None)
    if farmer is None:
        raise NotFound("No farmer profile is linked to this account.")
    return farmer


class FarmerProfileView(APIView):
    permission_classes = [IsFarmer]

    def get(self, request):
        farmer = farmer_for(request)
        planting = Planting.objects.filter(plot__farmer=farmer).select_related(
            "crop").order_by("-season__year").first()
        return Response({
            "full_name": farmer.full_name, "phone": farmer.phone or "", "sex": farmer.sex,
            "language": farmer.language, "area_acres": planting.plot.area_acres if planting else None,
            "crop_id": planting.crop_id if planting else None,
            "planting_date": planting.planting_date if planting else None,
        })

    def patch(self, request):
        farmer = farmer_for(request)
        data = FarmerProfileSerializer(data=request.data, partial=True)
        data.is_valid(raise_exception=True)
        values = data.validated_data
        for field in ("full_name", "phone", "sex", "language"):
            if field in values:
                setattr(farmer, field, values[field])
        farmer.save(update_fields=[field for field in (
            "full_name", "phone", "sex", "language") if field in values] + ["updated_at"])

        if "area_acres" in values or "crop_id" in values or "planting_date" in values:
            season = __import__("apps.advisory.selectors", fromlist=[
                                "current_season"]).current_season()
            if season is None:
                raise ValidationError(
                    "There is no active season to update farm details.")
            planting = Planting.objects.filter(
                plot__farmer=farmer, season=season).select_related("plot").first()
            if planting is None:
                if not {"area_acres", "crop_id", "planting_date"}.issubset(values):
                    raise ValidationError(
                        "area_acres, crop_id, and planting_date are required for a new crop record.")
                plot = Plot.objects.create(
                    farmer=farmer, area_acres=values["area_acres"])
                Planting.objects.create(
                    plot=plot, season=season, crop_id=values["crop_id"], planting_date=values["planting_date"])
            else:
                if "area_acres" in values:
                    planting.plot.area_acres = values["area_acres"]
                    planting.plot.save(
                        update_fields=["area_acres", "updated_at"])
                if "crop_id" in values:
                    planting.crop_id = values["crop_id"]
                if "planting_date" in values:
                    planting.planting_date = values["planting_date"]
                planting.save(
                    update_fields=["crop_id", "planting_date", "updated_at"])
        return self.get(request)


class FarmerDeclarationView(APIView):
    permission_classes = [IsFarmer]

    def post(self, request):
        farmer = farmer_for(request)
        data = FarmerDeclarationSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        try:
            crop = Crop.objects.get(pk=data.validated_data["crop_id"])
            declaration = declare(farmer=farmer, crop=crop,
                                  bags=data.validated_data["bags"], moisture=data.validated_data.get(
                                      "moisture_pct"),
                                  actor=request.user, via="web")
        except (Crop.DoesNotExist, DomainError) as error:
            if isinstance(error, Crop.DoesNotExist):
                raise ValidationError({"crop_id": "Unknown crop."})
            return Response({"detail": str(error)}, status=409)
        return Response({"id": declaration.id, "grade": declaration.grade}, status=201)
