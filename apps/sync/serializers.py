from rest_framework import serializers

from apps.farmers.serializers import CropSerializer

OP_TYPES = ["farmer.create", "declaration.create", "declaration.grade"]


class SyncOperationInputSerializer(serializers.Serializer):
    op_id = serializers.CharField(max_length=64)
    type = serializers.ChoiceField(choices=OP_TYPES)
    at = serializers.DateTimeField()
    payload = serializers.JSONField()


class SyncBatchRequestSerializer(serializers.Serializer):
    device_id = serializers.CharField(max_length=64)
    operations = SyncOperationInputSerializer(many=True)


class SyncResultSerializer(serializers.Serializer):
    op_id = serializers.CharField()
    status = serializers.ChoiceField(choices=["applied", "rejected"])
    reason = serializers.CharField(required=False)
    farmer_id = serializers.IntegerField(required=False)
    declaration_id = serializers.IntegerField(required=False)
    created = serializers.BooleanField(required=False)
    grade = serializers.CharField(required=False)


class SyncBatchResponseSerializer(serializers.Serializer):
    results = SyncResultSerializer(many=True)
    server_time = serializers.DateTimeField()


class VillageSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()


class BootstrapFarmerSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    full_name = serializers.CharField()
    village_id = serializers.IntegerField(source="village.id")
    phone = serializers.CharField(allow_null=True)


class OpenLotSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    crop_id = serializers.IntegerField(source="crop.id")
    crop = serializers.CharField(source="crop.name")
    bags = serializers.SerializerMethodField()
    min_bags = serializers.IntegerField()

    def get_bags(self, lot) -> int:
        from apps.market.services import sellable_bags

        return sellable_bags(lot)


class BootstrapSerializer(serializers.Serializer):
    parish_id = serializers.IntegerField()
    villages = VillageSerializer(many=True)
    crops = CropSerializer(many=True)
    farmers = BootstrapFarmerSerializer(many=True)
    open_lots = OpenLotSerializer(many=True)
