from apps.accounts.permissions import IsNationalAdmin
from apps.core.viewsets import AdminModelViewSet
from apps.market.admin_serializers import BuyerAdminSerializer
from apps.market.models import Buyer


class BuyerViewSet(AdminModelViewSet):
    queryset = Buyer.objects.select_related("user").order_by("name")
    serializer_class = BuyerAdminSerializer
    permission_classes = [IsNationalAdmin]
