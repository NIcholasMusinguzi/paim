from django.urls import path

from .views import DistrictParishesView, NationalMetricsView, TrendApproveView, TrendListView

urlpatterns = [
    path("metrics/national/", NationalMetricsView.as_view()),
    path("metrics/district/<int:district_id>/parishes/", DistrictParishesView.as_view()),
    path("trends/", TrendListView.as_view()),
    path("trends/<int:insight_id>/approve/", TrendApproveView.as_view()),
]
