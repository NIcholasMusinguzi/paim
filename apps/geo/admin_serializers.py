from rest_framework import serializers

from apps.geo.models import District, Parish, Subcounty, Village


class DistrictAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = District
        fields = ["id", "name", "region"]


class SubcountyAdminSerializer(serializers.ModelSerializer):
    district_name = serializers.CharField(source="district.name", read_only=True)

    class Meta:
        model = Subcounty
        fields = ["id", "district", "district_name", "name"]


class ParishAdminSerializer(serializers.ModelSerializer):
    subcounty_name = serializers.CharField(source="subcounty.name", read_only=True)
    district_name = serializers.CharField(source="subcounty.district.name", read_only=True)

    class Meta:
        model = Parish
        fields = ["id", "subcounty", "subcounty_name", "district_name", "name", "agro_zone", "lot_min_bags"]


class VillageAdminSerializer(serializers.ModelSerializer):
    parish_name = serializers.CharField(source="parish.name", read_only=True)

    class Meta:
        model = Village
        fields = ["id", "parish", "parish_name", "name"]
