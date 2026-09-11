from rest_framework import serializers

from apps.farmers.models import Crop, Farmer, Season
from apps.farmers.selectors import crop_ids_for, crop_names
from apps.farmers.services import FarmerError, set_current_crops


class CropAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = Crop
        fields = ["id", "name", "cycle_weeks"]


class SeasonAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = Season
        fields = ["id", "year", "season_no", "start_date", "end_date"]


class FarmerAdminSerializer(serializers.ModelSerializer):
    village_name = serializers.CharField(source="village.name", read_only=True)
    parish_name = serializers.CharField(source="village.parish.name", read_only=True)
    district_name = serializers.CharField(source="village.parish.subcounty.district.name", read_only=True)
    registered_by_name = serializers.CharField(source="registered_by.full_name", read_only=True, default=None, allow_null=True)
    user_phone = serializers.CharField(source="user.phone", read_only=True, default=None, allow_null=True)
    crops = serializers.SerializerMethodField()
    crop_ids = serializers.ListField(child=serializers.IntegerField(), required=False, write_only=True)

    class Meta:
        model = Farmer
        # NIN is deliberately excluded: hashing it and recording consent is
        # its own service (apps.farmers.services.set_nin) with its own
        # security handling, not something to bypass with generic CRUD.
        fields = ["id", "full_name", "sex", "phone", "language", "reach_channel",
                  "village", "village_name", "parish_name", "district_name",
                  "registered_by_name", "user_phone", "crops", "crop_ids"]

    def get_crops(self, farmer) -> list[str]:
        return crop_names(farmer)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["crop_ids"] = crop_ids_for(instance)
        return data

    def create(self, validated_data):
        crop_ids = validated_data.pop("crop_ids", None)
        validated_data["registered_by"] = self.context["request"].user
        farmer = super().create(validated_data)
        if crop_ids:
            try:
                set_current_crops(farmer=farmer, crop_ids=crop_ids)
            except FarmerError as error:
                raise serializers.ValidationError({"crop_ids": str(error)})
        return farmer

    def update(self, instance, validated_data):
        crop_ids = validated_data.pop("crop_ids", None)
        farmer = super().update(instance, validated_data)
        if crop_ids is not None:
            try:
                set_current_crops(farmer=farmer, crop_ids=crop_ids)
            except FarmerError as error:
                raise serializers.ValidationError({"crop_ids": str(error)})
        return farmer
