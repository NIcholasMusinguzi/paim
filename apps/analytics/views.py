from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import Role
from apps.analytics.exports import pdf_response, xlsx_response
from apps.analytics.models import (
    DistrictSeasonMetric,
    NationalSeasonMetric,
    ParishSeasonMetric,
    TrendInsight,
)
from apps.analytics.reports import BUILDERS
from apps.analytics.serializers import (
    NationalMetricsResponseSerializer,
    ParishMetricSerializer,
    TrendInsightSerializer,
)
from apps.analytics.trends import TrendApprovalError, approve_insight, pending_insights_for


class IsDistrictOrNationalAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated
                    and request.user.role in (Role.DISTRICT_OFFICER, Role.NATIONAL_ADMIN))


def _season_and_crop(request) -> tuple[str, str]:
    season_id = request.query_params.get("season")
    crop_id = request.query_params.get("crop")
    if not season_id or not crop_id:
        raise ValidationError("season and crop query parameters are required.")
    return season_id, crop_id


def _report_format(request) -> str:
    fmt = request.query_params.get("format", "json")
    if fmt not in ("json", "xlsx", "pdf"):
        raise ValidationError("format must be json, xlsx or pdf.")
    return fmt


_FORMAT_PARAM = OpenApiParameter(
    name="format", location=OpenApiParameter.QUERY, required=False,
    enum=["json", "xlsx", "pdf"], description="json (default), xlsx or pdf.")


def _maybe_file(fmt, filename, title, headers, table_rows, json_payload):
    if fmt == "xlsx":
        return xlsx_response(filename, title, headers, table_rows)
    if fmt == "pdf":
        return pdf_response(filename, title, headers, table_rows)
    return Response(json_payload)


class NationalMetricsView(APIView):
    permission_classes = [IsDistrictOrNationalAdmin]

    @extend_schema(responses={200: NationalMetricsResponseSerializer})
    def get(self, request):
        season_id, crop_id = _season_and_crop(request)
        districts = (
            DistrictSeasonMetric.objects.filter(
                season_id=season_id, crop_id=crop_id)
            .select_related("district").order_by("rank_national")
        )
        national = (
            NationalSeasonMetric.objects.filter(
                season_id=season_id, crop_id=crop_id).first()
        )
        return Response(NationalMetricsResponseSerializer({"districts": districts, "national": national}).data)


class DistrictParishesView(APIView):
    permission_classes = [IsDistrictOrNationalAdmin]

    @extend_schema(responses={200: ParishMetricSerializer(many=True)})
    def get(self, request, district_id):
        season_id, crop_id = _season_and_crop(request)
        rows = (
            ParishSeasonMetric.objects.filter(
                parish__subcounty__district_id=district_id, season_id=season_id, crop_id=crop_id)
            .select_related("parish").order_by("-pct_grade1")
        )
        return Response(ParishMetricSerializer(rows, many=True).data)


class KindReportView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(parameters=[_FORMAT_PARAM])
    def get(self, request, kind):
        builder = BUILDERS.get(kind)
        if builder is None:
            raise NotFound("Unknown report.")
        fmt = _report_format(request)
        filename, title, headers, payload, table = builder(
            request.user,
            season_id=request.query_params.get("season"),
            crop_id=request.query_params.get("crop"),
            district_id=request.query_params.get("district"),
        )
        return _maybe_file(fmt, filename, title, headers, table, payload)


class ScopedReportView(KindReportView):
    def get(self, request):
        return super().get(request, "scoped")


class AdvisoryReportView(KindReportView):
    def get(self, request):
        return super().get(request, "advisories")


class MarketReportView(KindReportView):
    def get(self, request):
        return super().get(request, "market")


class TrendListView(APIView):
    permission_classes = [IsDistrictOrNationalAdmin]

    @extend_schema(responses={200: TrendInsightSerializer(many=True)})
    def get(self, request):
        status_filter = request.query_params.get("status", "pending")
        if status_filter == "published":
            rows = TrendInsight.objects.filter(published_at__isnull=False).select_related(
                "crop", "approved_by").order_by("-published_at")
        else:
            rows = pending_insights_for(request.user)
        return Response(TrendInsightSerializer(rows, many=True).data)


class TrendApproveView(APIView):
    """An unapproved insight is unreachable from any client route or API
    call — this is the only endpoint that can make one visible to a farmer
    (IMPLEMENTATION.md section 7.6)."""

    permission_classes = [IsDistrictOrNationalAdmin]

    @extend_schema(request=None, responses={200: TrendInsightSerializer})
    def post(self, request, insight_id):
        get_object_or_404(TrendInsight, pk=insight_id)
        try:
            insight = approve_insight(
                insight_id=insight_id, actor=request.user)
        except TrendApprovalError as e:
            return Response({"detail": str(e)}, status=status.HTTP_409_CONFLICT)
        return Response(TrendInsightSerializer(insight).data)
