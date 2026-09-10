from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.market.services import sellable_bags


class ParishInfoSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    district = serializers.CharField(source="district.name")


class DashboardLotSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    crop = serializers.CharField(source="crop.name")
    status = serializers.CharField()
    bags = serializers.SerializerMethodField()
    min_bags = serializers.IntegerField()

    def get_bags(self, lot) -> int:
        return sellable_bags(lot)


class DashboardDeclarationSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    farmer_name = serializers.CharField(source="farmer.full_name")
    bags = serializers.IntegerField()
    grade = serializers.CharField()
    moisture_pct = serializers.DecimalField(
        max_digits=4, decimal_places=1, allow_null=True)
    created_at = serializers.DateTimeField()


class DashboardMetricsSerializer(serializers.Serializer):
    pct_grade1 = serializers.IntegerField()
    bags_declared = serializers.IntegerField()
    avg_price_per_kg = serializers.IntegerField(allow_null=True)
    farmers_active = serializers.IntegerField()
    computed_at = serializers.DateTimeField()


class ParishDashboardSerializer(serializers.Serializer):
    parish = ParishInfoSerializer()
    lot = DashboardLotSerializer(allow_null=True)
    declarations = DashboardDeclarationSerializer(many=True)
    metrics = DashboardMetricsSerializer(allow_null=True)


class BuyerLotSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    parish = serializers.CharField(source="parish.name")
    crop = serializers.CharField(source="crop.name")
    bags = serializers.SerializerMethodField()
    min_bags = serializers.IntegerField()
    opened_at = serializers.DateTimeField()

    def get_bags(self, lot) -> int:
        return sellable_bags(lot)


class BidSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    buyer_name = serializers.CharField(source="buyer.name")
    price_per_kg = serializers.IntegerField()
    terms = serializers.CharField()
    submitted_at = serializers.DateTimeField()


class LotDetailSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    parish = serializers.CharField(source="parish.name")
    crop = serializers.CharField(source="crop.name")
    status = serializers.CharField()
    bags = serializers.SerializerMethodField()
    min_bags = serializers.IntegerField()
    bid_count = serializers.SerializerMethodField()
    bids = serializers.SerializerMethodField()
    awarded_buyer = serializers.SerializerMethodField()
    awarded_price_per_kg = serializers.SerializerMethodField()

    def get_bags(self, lot) -> int:
        return sellable_bags(lot)

    def get_bid_count(self, lot) -> int:
        return getattr(lot, "_bid_count", lot.bids.count())

    @extend_schema_field(BidSerializer(many=True))
    def get_bids(self, lot):
        from apps.market.services import visible_bids

        return BidSerializer(visible_bids(lot, self.context["viewer"]), many=True).data

    def get_awarded_buyer(self, lot) -> str | None:
        bid = lot.awarded_bid if lot.awarded_bid_id else None
        return bid.buyer.name if bid else None

    def get_awarded_price_per_kg(self, lot) -> int | None:
        bid = lot.awarded_bid if lot.awarded_bid_id else None
        return bid.price_per_kg if bid else None


class BidInputSerializer(serializers.Serializer):
    price_per_kg = serializers.IntegerField(min_value=1)
    terms = serializers.CharField(max_length=160)


class AwardInputSerializer(serializers.Serializer):
    bid_id = serializers.IntegerField()
    committee_minute_ref = serializers.CharField(max_length=120)


class MarketPriceSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    item_name = serializers.CharField()
    category = serializers.CharField()
    price = serializers.IntegerField()
    unit = serializers.CharField()
    market = serializers.CharField()
    price_date = serializers.DateField()
    source = serializers.CharField()
