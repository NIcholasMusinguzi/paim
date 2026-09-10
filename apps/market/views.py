from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import serializers, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import Role
from apps.accounts.permissions import IsOfficer
from apps.accounts.scoping import parish_ids_for
from apps.geo.models import Parish
from apps.market.models import Bid, Buyer, Lot, MarketPrice
from apps.market.selectors import lots_for_viewer, open_lots, parish_dashboard_data
from apps.market.serializers import (
    AwardInputSerializer,
    BidInputSerializer,
    BuyerLotSerializer,
    LotDetailSerializer,
    MarketPriceSerializer,
    ParishDashboardSerializer,
)
from apps.market.services import DomainError, award_lot, submit_bid


class HealthSerializer(serializers.Serializer):
    status = serializers.CharField()


class HealthView(APIView):
    authentication_classes = []
    permission_classes = []

    @extend_schema(responses={200: HealthSerializer})
    def get(self, request):
        return Response({"status": "ok"})


class DailyMarketPriceView(APIView):
    @extend_schema(responses={200: MarketPriceSerializer(many=True)})
    def get(self, request):
        price_date = request.query_params.get("date", timezone.localdate())
        prices = MarketPrice.objects.filter(
            price_date=price_date).order_by("category", "item_name")
        return Response(MarketPriceSerializer(prices, many=True).data)


class ParishDashboardView(APIView):
    # parish_ids_for() alone is not enough: a farmer's own account also
    # resolves to their parish (it needs a scope for /farmer/home/), but
    # the role matrix reserves the parish dashboard for officers only.
    permission_classes = [IsOfficer]

    @extend_schema(responses={200: ParishDashboardSerializer})
    def get(self, request, parish_id):
        # Same scoping rule as the WebSocket consumer (apps/realtime/consumers.py)
        # — one rule, both transports, so they can never diverge.
        if not parish_ids_for(request.user).filter(id=parish_id).exists():
            raise PermissionDenied("You do not have access to this parish.")
        parish = get_object_or_404(Parish.objects.select_related(
            "subcounty__district"), pk=parish_id)
        return Response(ParishDashboardSerializer(parish_dashboard_data(parish)).data)


class IsBuyer(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == Role.BUYER)


def _may_view_lot(user, lot) -> bool:
    if user.role == Role.BUYER:
        return True
    return parish_ids_for(user).filter(id=lot.parish_id).exists()


class BuyerLotListView(APIView):
    permission_classes = [IsBuyer]

    @extend_schema(responses={200: BuyerLotSerializer(many=True)})
    def get(self, request):
        return Response(BuyerLotSerializer(open_lots(), many=True).data)


class LotListView(APIView):
    @extend_schema(responses={200: LotDetailSerializer(many=True)})
    def get(self, request):
        return Response(
            LotDetailSerializer(
                lots_for_viewer(request.user), many=True, context={"viewer": request.user},
            ).data
        )


class LotDetailView(APIView):
    @extend_schema(responses={200: LotDetailSerializer})
    def get(self, request, lot_id):
        lot = get_object_or_404(
            Lot.objects.select_related("parish", "crop"), pk=lot_id)
        if not _may_view_lot(request.user, lot):
            raise PermissionDenied("You do not have access to this lot.")
        return Response(LotDetailSerializer(lot, context={"viewer": request.user}).data)


class BidSubmitView(APIView):
    permission_classes = [IsBuyer]

    @extend_schema(request=BidInputSerializer, responses={201: LotDetailSerializer})
    def post(self, request, lot_id):
        data = BidInputSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        lot = get_object_or_404(Lot, pk=lot_id)
        buyer = get_object_or_404(Buyer, user=request.user)
        try:
            submit_bid(lot=lot, buyer=buyer, **data.validated_data)
        except DomainError as e:
            return Response({"detail": str(e)}, status=status.HTTP_409_CONFLICT)
        return Response(LotDetailSerializer(lot, context={"viewer": request.user}).data,
                        status=status.HTTP_201_CREATED)


class IsParishChiefOrSubcountyOfficer(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated
                    and request.user.role in (Role.PARISH_CHIEF, Role.SUBCOUNTY_OFFICER))


class AwardView(APIView):
    permission_classes = [IsParishChiefOrSubcountyOfficer]

    @extend_schema(request=AwardInputSerializer, responses={200: LotDetailSerializer})
    def post(self, request, lot_id):
        lot = get_object_or_404(Lot, pk=lot_id)
        if not parish_ids_for(request.user).filter(id=lot.parish_id).exists():
            raise PermissionDenied("You do not have access to this parish.")
        data = AwardInputSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        try:
            award_lot(lot_id=lot.id, bid_id=data.validated_data["bid_id"], actor=request.user,
                      minute_ref=data.validated_data["committee_minute_ref"])
        except (DomainError, Bid.DoesNotExist) as e:
            return Response({"detail": str(e)}, status=status.HTTP_409_CONFLICT)
        lot.refresh_from_db()
        return Response(LotDetailSerializer(lot, context={"viewer": request.user}).data)
