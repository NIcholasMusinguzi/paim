from rest_framework import serializers

from apps.farmers.selectors import crop_names
from apps.market.services import sellable_bags


class FarmerSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    full_name = serializers.CharField()
    village = serializers.CharField(source="village.name")
    parish = serializers.CharField(source="village.parish.name")


class FarmerDirectorySerializer(serializers.Serializer):
    id = serializers.IntegerField()
    full_name = serializers.CharField()
    sex = serializers.CharField()
    phone = serializers.CharField(allow_null=True, allow_blank=True)
    village = serializers.CharField(source="village.name")
    parish = serializers.CharField(source="village.parish.name")
    subcounty = serializers.CharField(source="village.parish.subcounty.name")
    district = serializers.CharField(source="village.parish.subcounty.district.name")
    crops = serializers.SerializerMethodField()

    def get_crops(self, farmer) -> list[str]:
        return crop_names(farmer)


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


class FarmerProfileSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=120, required=False)
    phone = serializers.CharField(
        max_length=20, allow_blank=True, required=False)
    sex = serializers.ChoiceField(choices=["F", "M"], required=False)
    language = serializers.CharField(max_length=16, required=False)
    area_acres = serializers.DecimalField(
        max_digits=5, decimal_places=2, required=False)
    crop_id = serializers.IntegerField(required=False)
    crop_ids = serializers.ListField(child=serializers.IntegerField(), required=False)
    planting_date = serializers.DateField(required=False)


class FarmerDeclarationSerializer(serializers.Serializer):
    crop_id = serializers.IntegerField()
    bags = serializers.IntegerField(min_value=1, max_value=200)
    moisture_pct = serializers.DecimalField(
        max_digits=4, decimal_places=1, required=False, allow_null=True)
