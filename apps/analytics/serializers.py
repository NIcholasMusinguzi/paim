from rest_framework import serializers


class ParishMetricSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    parish_id = serializers.IntegerField()
    parish = serializers.CharField()
    farmers_registered = serializers.IntegerField()
    farmers_active = serializers.IntegerField()
    bags_declared = serializers.IntegerField()
    pct_grade1 = serializers.IntegerField()
    avg_price_per_kg = serializers.IntegerField(allow_null=True)
    agent_reach = serializers.IntegerField()
    live = serializers.BooleanField()
    computed_at = serializers.DateTimeField(allow_null=True)


class SeasonBarSerializer(serializers.Serializer):
    season_id = serializers.IntegerField()
    label = serializers.CharField()
    pct_grade1 = serializers.IntegerField()
    avg_price_per_kg = serializers.IntegerField(allow_null=True)


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
    scope_name = serializers.SerializerMethodField()
    crop = serializers.CharField(source="crop.name")
    metric = serializers.CharField()
    direction = serializers.CharField()
    magnitude = serializers.DecimalField(max_digits=6, decimal_places=2)
    message = serializers.CharField()
    approved_by = serializers.CharField(source="approved_by.full_name", allow_null=True, default=None)
    published_at = serializers.DateTimeField(allow_null=True)

    def get_scope_name(self, insight) -> str:
        from apps.accounts.models import ScopeLevel
        from apps.geo.models import District, Parish

        if insight.scope_level == ScopeLevel.NATIONAL:
            return "National"
        if insight.scope_level == ScopeLevel.DISTRICT:
            name = District.objects.filter(pk=insight.scope_id).values_list("name", flat=True).first()
            return f"{name} district" if name else "District"
        name = Parish.objects.filter(pk=insight.scope_id).values_list("name", flat=True).first()
        return name or "Parish"


class AdvisoryReportRowSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    parish = serializers.CharField()
    requester = serializers.CharField()
    status = serializers.CharField()
    response_count = serializers.IntegerField()
    message = serializers.CharField()


class MarketReportRowSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    parish = serializers.CharField()
    crop = serializers.CharField()
    status = serializers.CharField()
    bags = serializers.IntegerField()
    bid_count = serializers.IntegerField()
    awarded_buyer = serializers.CharField(allow_null=True)
    awarded_price_per_kg = serializers.IntegerField(allow_null=True)

