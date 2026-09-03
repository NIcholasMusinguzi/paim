from rest_framework import serializers


class ParishMetricSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    parish_id = serializers.IntegerField()
    parish = serializers.CharField(source="parish.name")
    farmers_registered = serializers.IntegerField()
    farmers_active = serializers.IntegerField()
    bags_declared = serializers.IntegerField()
    pct_grade1 = serializers.IntegerField()
    avg_price_per_kg = serializers.IntegerField(allow_null=True)
    computed_at = serializers.DateTimeField()


class DistrictMetricSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    district_id = serializers.IntegerField()
    district = serializers.CharField(source="district.name")
    farmers_registered = serializers.IntegerField()
    farmers_active = serializers.IntegerField()
    bags_declared = serializers.IntegerField()
    pct_grade1 = serializers.IntegerField()
    avg_price_per_kg = serializers.IntegerField(allow_null=True)
    parishes_reporting = serializers.IntegerField()
    rank_national = serializers.IntegerField(allow_null=True)
    computed_at = serializers.DateTimeField()


class NationalMetricSerializer(serializers.Serializer):
    farmers_registered = serializers.IntegerField()
    farmers_active = serializers.IntegerField()
    bags_declared = serializers.IntegerField()
    pct_grade1 = serializers.IntegerField()
    avg_price_per_kg = serializers.IntegerField(allow_null=True)
    districts_reporting = serializers.IntegerField()
    computed_at = serializers.DateTimeField()


class NationalMetricsResponseSerializer(serializers.Serializer):
    districts = DistrictMetricSerializer(many=True)
    national = NationalMetricSerializer(allow_null=True)


class TrendInsightSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    scope_level = serializers.CharField()
    scope_id = serializers.IntegerField(allow_null=True)
    crop = serializers.CharField(source="crop.name")
    metric = serializers.CharField()
    direction = serializers.CharField()
    magnitude = serializers.DecimalField(max_digits=6, decimal_places=2)
    message = serializers.CharField()
    approved_by = serializers.CharField(source="approved_by.full_name", allow_null=True, default=None)
    published_at = serializers.DateTimeField(allow_null=True)
