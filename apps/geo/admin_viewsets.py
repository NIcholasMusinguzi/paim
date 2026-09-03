from apps.accounts.permissions import IsNationalAdmin
from apps.core.viewsets import AdminModelViewSet
from apps.geo.admin_serializers import (
    DistrictAdminSerializer,
    ParishAdminSerializer,
    SubcountyAdminSerializer,
    VillageAdminSerializer,
)
from apps.geo.models import District, Parish, Subcounty, Village


class DistrictViewSet(AdminModelViewSet):
    queryset = District.objects.order_by("name")
    serializer_class = DistrictAdminSerializer
    permission_classes = [IsNationalAdmin]


class SubcountyViewSet(AdminModelViewSet):
    queryset = Subcounty.objects.select_related("district").order_by("name")
    serializer_class = SubcountyAdminSerializer
    permission_classes = [IsNationalAdmin]


class ParishViewSet(AdminModelViewSet):
    queryset = Parish.objects.select_related("subcounty__district").order_by("name")
    serializer_class = ParishAdminSerializer
    permission_classes = [IsNationalAdmin]


class VillageViewSet(AdminModelViewSet):
    queryset = Village.objects.select_related("parish").order_by("name")
    serializer_class = VillageAdminSerializer
    permission_classes = [IsNationalAdmin]
