from django.urls import path

from .views import (
    AdvisoryReportView,
    DistrictParishesView,
    DistrictSeasonBarsView,
    KindReportView,
    MarketReportView,
    NationalMetricsView,
    ScopedReportView,
    TrendApproveView,
    TrendListView,
)

urlpatterns = [
    path("metrics/national/", NationalMetricsView.as_view()),
    path("metrics/district/<int:district_id>/parishes/",
         DistrictParishesView.as_view()),
    path("metrics/district/<int:district_id>/seasons/",
         DistrictSeasonBarsView.as_view()),
    path("reports/scoped/", ScopedReportView.as_view()),
    path("reports/advisories/", AdvisoryReportView.as_view()),
    path("reports/market/", MarketReportView.as_view()),
    path("reports/<str:kind>/", KindReportView.as_view()),
    path("trends/", TrendListView.as_view()),
    path("trends/<int:insight_id>/approve/", TrendApproveView.as_view()),
]
