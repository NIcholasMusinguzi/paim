from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import ScopeLevel
from apps.accounts.scoping import parish_ids_for
from apps.geo.models import Parish, Village
from apps.geo.weather import WeatherError, weather_for_parish


class ParishListSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    district = serializers.CharField(source="district.name")
    district_id = serializers.IntegerField(source="subcounty.district_id")


class ParishListView(APIView):
    @extend_schema(responses={200: ParishListSerializer(many=True)})
    def get(self, request):
        parishes = (
            Parish.objects.filter(id__in=parish_ids_for(request.user))
            .select_related("subcounty__district")
            .order_by("name")
        )
        return Response(ParishListSerializer(parishes, many=True).data)


class VillageListSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    parish = serializers.CharField(source="parish.name")
    district = serializers.CharField(source="parish.district.name")


class PublicVillageListView(APIView):
    """Unauthenticated on purpose: a farmer signing up has no account yet
    and needs to pick their village to register against. Geography names
    are not sensitive — only farmer records themselves are."""

    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(responses={200: VillageListSerializer(many=True)})
    def get(self, request):
        villages = Village.objects.select_related("parish__subcounty__district").order_by("name")
        return Response(VillageListSerializer(villages, many=True).data)


class WeatherSerializer(serializers.Serializer):
    place = serializers.CharField()
    temp_c = serializers.IntegerField()
    summary = serializers.CharField()
    icon = serializers.CharField()
    humidity = serializers.IntegerField()
    rain_mm = serializers.IntegerField()
    wind_kmh = serializers.IntegerField()
    forecast = serializers.ListField()


class WeatherView(APIView):
    @extend_schema(responses={200: WeatherSerializer})
    def get(self, request):
        parish = None
        parish_id = request.query_params.get("parish_id")
        if parish_id:
            parish = get_object_or_404(
                Parish.objects.select_related("subcounty__district"), pk=parish_id)
        elif request.user.scope_level == ScopeLevel.PARISH and request.user.scope_id:
            parish = Parish.objects.select_related("subcounty__district").filter(
                pk=request.user.scope_id).first()
        try:
            return Response(WeatherSerializer(weather_for_parish(parish)).data)
        except WeatherError as exc:
            return Response({"detail": str(exc)}, status=502)

