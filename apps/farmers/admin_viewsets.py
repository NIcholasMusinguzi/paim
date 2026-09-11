from apps.accounts.permissions import IsNationalAdmin
from apps.core.viewsets import AdminModelViewSet
from apps.farmers.admin_serializers import (
    CropAdminSerializer,
    FarmerAdminSerializer,
    SeasonAdminSerializer,
)
from apps.farmers.models import Crop, Farmer, Season


class CropViewSet(AdminModelViewSet):
    queryset = Crop.objects.order_by("name")
    serializer_class = CropAdminSerializer
    permission_classes = [IsNationalAdmin]


class SeasonViewSet(AdminModelViewSet):
    queryset = Season.objects.order_by("-year", "-season_no")
    serializer_class = SeasonAdminSerializer
    permission_classes = [IsNationalAdmin]


class FarmerViewSet(AdminModelViewSet):
    queryset = Farmer.objects.select_related(
        "village__parish__subcounty__district", "registered_by", "user"
    ).prefetch_related("plots__plantings__crop").order_by("full_name")
    serializer_class = FarmerAdminSerializer
    permission_classes = [IsNationalAdmin]
