from django.urls import path

from apps.market.views import (
    AwardView,
    BidSubmitView,
    BuyerLotListView,
    HealthView,
    DailyMarketPriceView,
    LotDetailView,
    ParishDashboardView,
)

urlpatterns = [
    path("healthz/", HealthView.as_view()),
    path("market-prices/daily/", DailyMarketPriceView.as_view()),
    path("parish/<int:parish_id>/dashboard/", ParishDashboardView.as_view()),
    path("buyer/lots/", BuyerLotListView.as_view()),
    path("lots/<int:lot_id>/", LotDetailView.as_view()),
    path("lots/<int:lot_id>/bids/", BidSubmitView.as_view()),
    path("lots/<int:lot_id>/award/", AwardView.as_view()),
]
