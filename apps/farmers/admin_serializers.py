from rest_framework import serializers

from apps.farmers.models import Crop, Farmer, Season


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

    class Meta:
        model = Farmer
        # NIN is deliberately excluded: hashing it and recording consent is
        # its own service (apps.farmers.services.set_nin) with its own
        # security handling, not something to bypass with generic CRUD.
        fields = ["id", "full_name", "sex", "phone", "language", "reach_channel",
                  "village", "village_name", "parish_name", "district_name",
                  "registered_by_name", "user_phone"]

    def create(self, validated_data):
        validated_data["registered_by"] = self.context["request"].user
        return super().create(validated_data)
