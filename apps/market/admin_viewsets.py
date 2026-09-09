from apps.accounts.permissions import IsNationalAdmin
from apps.core.viewsets import AdminModelViewSet
from apps.market.admin_serializers import BidAdminSerializer, BuyerAdminSerializer, MarketPriceAdminSerializer
from apps.market.models import Bid, Buyer, MarketPrice


class BuyerViewSet(AdminModelViewSet):
    queryset = Buyer.objects.select_related("user").order_by("name")
    serializer_class = BuyerAdminSerializer
    permission_classes = [IsNationalAdmin]


class BidViewSet(AdminModelViewSet):
    queryset = Bid.objects.select_related(
        "buyer", "lot__crop", "lot__parish").order_by("-submitted_at")
    serializer_class = BidAdminSerializer
    permission_classes = [IsNationalAdmin]
    http_method_names = ["get", "head", "options"]


class MarketPriceViewSet(AdminModelViewSet):
    queryset = MarketPrice.objects.order_by(
        "-price_date", "category", "item_name")
    serializer_class = MarketPriceAdminSerializer
    permission_classes = [IsNationalAdmin]
