from rest_framework import serializers

from apps.market.services import sellable_bags


class FarmerSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    full_name = serializers.CharField()
    village = serializers.CharField(source="village.name")
    parish = serializers.CharField(source="village.parish.name")


class AdviceSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    crop = serializers.CharField(source="crop.name")
    body = serializers.CharField()
    source = serializers.CharField()
    week_from = serializers.IntegerField()
    week_to = serializers.IntegerField()


class LotSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    crop = serializers.CharField(source="crop.name")
    status = serializers.CharField()
    bags = serializers.SerializerMethodField()
    min_bags = serializers.IntegerField()

    def get_bags(self, lot) -> int:
        return sellable_bags(lot)


class PriceSerializer(serializers.Serializer):
    crop = serializers.CharField(source="crop.name")
    avg_price_per_kg = serializers.IntegerField()
    computed_at = serializers.DateTimeField()


class DeclarationSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    crop = serializers.CharField(source="lot.crop.name")
    bags = serializers.IntegerField()
    grade = serializers.CharField()
    lot_status = serializers.CharField(source="lot.status")
    created_at = serializers.DateTimeField()


class TrendSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    crop = serializers.CharField(source="crop.name")
    message = serializers.CharField()
    published_at = serializers.DateTimeField()


class FarmerHomeSerializer(serializers.Serializer):
    farmer = FarmerSerializer()
    advice = AdviceSerializer(many=True)
    lots = LotSerializer(many=True)
    prices = PriceSerializer(many=True)
    declarations = DeclarationSerializer(many=True)
    trends = TrendSerializer(many=True)


class SeasonSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    year = serializers.IntegerField()
    season_no = serializers.IntegerField()


class CropSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()


class ReferenceDataSerializer(serializers.Serializer):
    seasons = SeasonSerializer(many=True)
    crops = CropSerializer(many=True)
